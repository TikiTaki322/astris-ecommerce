from django.template.loader import render_to_string
from django.views.generic.edit import FormView
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, render

from accounts.utils import get_user_by_email_verification_token, link_lifetime_check, invalidate_all_user_sessions
from accounts.forms import UserPasswordCheckForm, UserSetPasswordForm, UserPasswordResetForm
from accounts.services.email_sender import send_email_via_resend

from shared.utils import extract_audit_data_from_request

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class UserPasswordChangeView(FormView):
    form_class = UserPasswordCheckForm
    template_name = 'accounts/password_change_request_validation.html'

    def form_valid(self, form):
        current = form.cleaned_data['password']

        user = self.request.user
        if not user.check_password(current):
            form.add_error('password', 'Wrong password')
            return self.form_invalid(form)

        user.refresh_verification_token()  # creation token, timestamp and saving in DB
        token = user.email_verification_token

        info = extract_audit_data_from_request(self.request)
        ip_address = info['ip_address']
        user_agent = info['user_agent']
        timestamp = info['timestamp']

        password_change_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:confirm_password_change') + f'?token={token}'
        )

        html_content = render_to_string('emails/password_change_request.html', {
            'password_change_url': password_change_url,
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        text_content = render_to_string('emails/password_change_request.txt', {
            'password_change_url': password_change_url,
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        try:
            send_email_via_resend(
                to_emails=user.email,
                subject='Password changing on Rawpapers',
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.warning(f'Password change request email failed: {user.email} | {e}\n\n')
            return self.form_invalid(form)

        return redirect(reverse('accounts:email_sent'))


class UserPasswordChangeConfirmView(FormView):
    form_class = UserSetPasswordForm
    template_name = 'accounts/password_change_request_processing.html'

    def dispatch(self, request, *args, **kwargs):
        token = request.GET.get('token')
        self.user = get_user_by_email_verification_token(token)

        if not self.user or not link_lifetime_check(self.user.email_sent_at):
            return render(request, 'accounts/link_error.html', {'message': 'This link has expired or is invalid.'},
                          status=403)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user  # necessarily for SetPasswordForm
        return kwargs

    def form_valid(self, form):
        new_password = form.cleaned_data['new_password1']
        if self.user.check_password(new_password):
            form.add_error('new_password1', 'The new password cannot be the same as the old one.')
            return self.form_invalid(form)

        form.save()
        self.user.email_verification_token = None
        self.user.save()
        invalidate_all_user_sessions(self.user)

        info = extract_audit_data_from_request(self.request)
        ip_address = info['ip_address']
        user_agent = info['user_agent']
        timestamp = info['timestamp']

        html_content = render_to_string('emails/password_changed_notification.html', {
            'username': self.user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        text_content = render_to_string('emails/password_changed_notification.txt', {
            'username': self.user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        try:
            send_email_via_resend(
                to_emails=self.user.email,
                subject='Password changed on Rawpapers',
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.warning(f'Password change notification email failed: {self.user.email} | {e}\n\n')

        return redirect(f"{reverse('accounts:login')}?info=password_changed")


class UserPasswordResetView(FormView):
    form_class = UserPasswordResetForm
    template_name = 'accounts/password_reset_request.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # not giving an info about email existence, returning fake answer
            return redirect(reverse('accounts:email_sent'))

        user.refresh_verification_token()
        token = user.email_verification_token

        info = extract_audit_data_from_request(self.request)
        ip_address = info['ip_address']
        user_agent = info['user_agent']
        timestamp = info['timestamp']

        password_reset_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:confirm_password_change') + f'?token={token}'
        )

        html_content = render_to_string('emails/password_reset_request.html', {
            'password_reset_url': password_reset_url,
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        text_content = render_to_string('emails/password_reset_request.txt', {
            'password_reset_url': password_reset_url,
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        try:
            send_email_via_resend(
                to_emails=user.email,
                subject='Reset password on Rawpapers',
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.warning(f'Password reset email failed: {user.email} | {e}\n\n')

        return redirect(reverse('accounts:email_sent'))