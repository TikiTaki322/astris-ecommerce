from django.template.loader import render_to_string
from django.utils.dateparse import parse_datetime
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse, reverse_lazy


from accounts.services.email_sender import send_email_via_resend
from accounts.forms import UserRegistrationForm

from accounts.utils import generate_email_verification_token, link_lifetime_check
from core.services.order_builder import OrderBuilderService

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class UserRegisterView(FormView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password1']
        email_sent_at = timezone.now().isoformat()  # datetime to str

        # Email confirmation link
        token = generate_email_verification_token()
        verify_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:confirm_register') + f'?token={token}'
        )

        html_content = render_to_string('emails/registration_request.html', {
            'verify_url': verify_url,
            'username': username,
        })
        text_content = render_to_string('emails/registration_request.txt', {
            'verify_url': verify_url,
            'username': username,
        })

        try:
            send_email_via_resend(
                to_emails=email,
                subject='Register account on Rawpapers',
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.warning(f'Registration request email failed: {email} | {e}\n\n')
            return self.form_invalid(form)

        # Temporary saving user-registration form data within session
        self.request.session['pending_user'] = {
            'username': username,
            'email': email,
            'password': password,
            'token': token,
            'email_sent_at': email_sent_at,
        }

        return redirect(reverse('accounts:email_sent'))


class UserRegisterConfirmView(TemplateView):
    template_name = 'accounts/link_error.html'

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        data = request.session.get('pending_user')

        if not token or not data or token != data.get('token'):
            del request.session['pending_user']
            return self.render_to_response({'message': 'Invalid token or expired session.'})

        logger.warning(f"Attempt to activate: {data['email']}")

        email_sent_at = parse_datetime(data['email_sent_at'])  # str to datetime
        if not link_lifetime_check(email_sent_at):
            logger.warning(f"Verification link has been expired: {data['email']}\n\n")
            del request.session['pending_user']
            return self.render_to_response({'message': 'Verification link has been expired.'})

        user = User(
            username=data['username'],
            email=data['email'],
            email_verified=True,
            email_verification_token=None,
            email_sent_at=email_sent_at,
        )
        user.set_password(data['password'])
        user.save()
        logger.warning(f'Email verified: {user.email} | User created: {user.username}\n\n')

        session_order = request.session.get('session_order', {})
        if session_order:
            _ = OrderBuilderService(session_order, user).build()  # Build an order based on the session
            del request.session['session_order']
        del request.session['pending_user']

        html_content = render_to_string('emails/registration_confirmed_notification.html', {
            'username': user.username,
        })

        text_content = render_to_string('emails/registration_confirmed_notification.txt', {
            'username': user.username,
        })

        try:
            send_email_via_resend(
                to_emails=user.email,
                subject="Account registered on Rawpapers",
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.warning(f'Registration confirm email failed: {user.email} | {e}\n\n')

        return redirect(f"{reverse('accounts:login')}?info=account_created")