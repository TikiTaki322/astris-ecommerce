from django.template.loader import render_to_string
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect

from accounts.utils import get_user_by_email_verification_token, link_lifetime_check, invalidate_all_user_sessions
from accounts.services.email_sender import send_email_via_resend
from accounts.forms import UserEmailUpdateForm

from shared.utils import extract_audit_data_from_request

import logging

logger = logging.getLogger(__name__)


class UserEmailUpdateView(FormView):
    form_class = UserEmailUpdateForm
    template_name = 'accounts/email_change_request.html'

    def form_valid(self, form):
        new_email = form.cleaned_data['new_email']
        current = form.cleaned_data['password']
        user = self.request.user

        if not user.check_password(current):
            form.add_error('password', 'Wrong password')
            return self.form_invalid(form)

        user.refresh_verification_token()  # creation token, timestamp and saving in DB
        token = user.email_verification_token
        change_email_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:confirm_email_update') + f'?token={token}&new_email={new_email}'
        )

        info = extract_audit_data_from_request(self.request)
        ip_address = info['ip_address']
        user_agent = info['user_agent']
        timestamp = info['timestamp']

        html_content = render_to_string('emails/email_reassign_initiating.html', {
            'change_email_url': change_email_url,
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        text_content = render_to_string('emails/email_reassign_initiating.txt', {
            'change_email_url': change_email_url,
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        try:
            send_email_via_resend(
                to_emails=new_email,
                subject='Updating email address on Rawpapers',
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.warning(f'Update post address email failed: {new_email} | {e}\n\n')
            return self.form_invalid(form)

        return redirect(reverse('accounts:email_sent'))


class UserEmailUpdateConfirmView(TemplateView):
    template_name = 'accounts/link_error.html'

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        new_email = request.GET.get('new_email')
        if not token or not new_email:
            return self.render_to_response({'message': 'Invalid request.'})

        user = get_user_by_email_verification_token(token)
        if not user or not link_lifetime_check(user.email_sent_at):
            return self.render_to_response({'message': 'This link has expired or is invalid.'})

        old_email = user.email
        user.email = new_email
        user.email_verification_token = None
        user.save()
        invalidate_all_user_sessions(user)

        info = extract_audit_data_from_request(request)
        ip_address = info['ip_address']
        user_agent = info['user_agent']
        timestamp = info['timestamp']

        html_content = render_to_string('emails/email_reassigned_notification.html', {
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        text_content = render_to_string('emails/email_reassigned_notification.txt', {
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp
        })

        try:
            send_email_via_resend(
                to_emails=[old_email, new_email],
                subject='Updated email address on Rawpapers',
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.warning(f'Changed post address notification email failed: {[old_email, new_email]} | {e}\n\n')

        return redirect(f"{reverse('accounts:login')}?info=email_changed")