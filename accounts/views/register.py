import logging

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from accounts.forms import UserRegistrationForm
from accounts.utils import generate_verification_token, link_lifetime_check
from core.services.order_builder import OrderBuilderService
from shared.tasks import send_email_task

logger = logging.getLogger(__name__)
User = get_user_model()


class UserRegisterView(FormView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register_form.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password1']

        # generate data
        token = generate_verification_token()
        email_sent_at = timezone.now().isoformat()  # datetime to str

        verify_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:confirm_register') + f'?token={token}'
        )

        context = {
            'verify_url': verify_url,
            'email': email,
        }

        # saving into session before sending
        self.request.session['pending_user'] = {
            'email': email,
            'password': password,
            'token': token,
            'email_sent_at': email_sent_at,
        }

        # asynchronous sending via Celery
        send_email_task.delay(
            email_type='registration',
            to_emails=email,
            context=context
        )

        # redirect without result awaiting
        return redirect(reverse('accounts:email_sent'))


class UserRegisterConfirmView(TemplateView):
    template_name = 'accounts/link_error.html'

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        data = request.session.get('pending_user')

        if not token or not data or token != data.get('token'):
            request.session.pop('pending_user', None)
            logger.warning(f"Verification attempt failed: {data['email']}")
            return self.render_to_response({'message': 'Invalid token or expired session'})

        if User.objects.filter(email=data['email']).exists():
            request.session.pop('pending_user', None)
            logger.warning(f"Verification attempt failed: {data['email']}")
            return self.render_to_response({'message': 'Email already in use'})

        email_sent_at = parse_datetime(data['email_sent_at'])  # str to datetime
        if not link_lifetime_check(email_sent_at):
            request.session.pop('pending_user', None)
            logger.warning(f"Verification attempt failed: {data['email']}")
            return self.render_to_response({'message': 'Verification link has been expired.'})

        user = User(
            email=data['email'],
            email_verified=True
        )
        user.set_password(data['password'])
        user.save()

        logger.info(f'Verification attempt succeeded: {user.email}')

        if session_order := request.session.get('session_order', {}):
            OrderBuilderService(session_order=session_order, user=user).build()  # Create order based on the session
            del request.session['session_order']
        del request.session['pending_user']

        return redirect(f"{reverse('accounts:login')}?info=account_created")