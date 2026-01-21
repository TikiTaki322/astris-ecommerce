import logging

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from accounts.forms import UserEmailUpdateForm
from accounts.utils import get_user_by_verification_token, link_lifetime_check, invalidate_all_user_sessions
from shared.permissions.mixins import AuthRequiredMixin
from shared.tasks import send_email_task
from shared.utils import extract_audit_data_from_request

logger = logging.getLogger(__name__)
User = get_user_model()


class UserEmailChangeView(AuthRequiredMixin, FormView):
    form_class = UserEmailUpdateForm
    template_name = 'accounts/email_address_change_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        new_email = form.cleaned_data['new_email']

        user = self.request.user
        token = user.refresh_verification_token()  # creation token, timestamp and saving in DB
        info = extract_audit_data_from_request(self.request)

        email_change_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:confirm_email_change') + f'?token={token}&new_email={new_email}'
        )

        context = {
            'email_change_url': email_change_url,
            'email': user.email,
            'new_email': new_email,
            'ip_address': info['ip_address'],
            'user_agent': info['user_agent'],
            'timestamp': info['timestamp']
        }

        send_email_task.delay(
            email_type='email_change',
            to_emails=user.email,
            context=context
        )

        return redirect(reverse('accounts:email_sent'))


class UserEmailChangeConfirmView(TemplateView):
    template_name = 'accounts/link_error.html'

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        new_email = request.GET.get('new_email')
        if not (token and new_email):
            return self.render_to_response({'message': 'Invalid request'})

        if User.objects.filter(email=new_email).exists():
            return self.render_to_response({'message': 'Email already in use'})

        user = get_user_by_verification_token(token)
        if not (user and link_lifetime_check(user.email_sent_at)):
            return self.render_to_response({'message': 'This link has expired or is invalid'})

        user.email = new_email
        user.save(update_fields=['email'])

        user.eliminate_verification_token()
        invalidate_all_user_sessions(user)

        return redirect(f"{reverse('accounts:login')}?info=email_changed")