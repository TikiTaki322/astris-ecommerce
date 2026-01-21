import logging

from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView

from accounts.forms import UserPasswordCheckForm, UserSetPasswordForm, UserPasswordResetForm
from accounts.utils import get_user_by_verification_token, link_lifetime_check, invalidate_all_user_sessions
from shared.permissions.mixins import AuthRequiredMixin
from shared.tasks import send_email_task
from shared.utils import extract_audit_data_from_request

logger = logging.getLogger(__name__)
User = get_user_model()


class UserPasswordChangeView(AuthRequiredMixin, FormView):
    form_class = UserPasswordCheckForm
    template_name = 'accounts/password_change_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        token = user.refresh_verification_token()  # creation token, timestamp and saving in DB
        info = extract_audit_data_from_request(self.request)

        password_change_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:new_password_setup') + f'?token={token}'
        )

        context = {
            'password_change_url': password_change_url,
            'email': user.email,
            'ip_address': info['ip_address'],
            'user_agent': info['user_agent'],
            'timestamp': info['timestamp']
        }

        send_email_task.delay(
            email_type='password_change',
            to_emails=user.email,
            context=context
        )

        return redirect(reverse('accounts:email_sent'))


class UserNewPasswordSetupView(FormView):
    form_class = UserSetPasswordForm
    template_name = 'accounts/new_password_setup_form.html'

    def dispatch(self, request, *args, **kwargs):
        token = request.GET.get('token')
        self.user = get_user_by_verification_token(token)

        if not self.user or not link_lifetime_check(self.user.email_sent_at):
            return render(request, 'accounts/link_error.html', {'message': 'This link has expired or is invalid'},
                          status=403)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user  # necessarily for SetPasswordForm (transmitting user instance to form)
        return kwargs

    def form_valid(self, form):
        form.save()
        self.user.save(update_fields=['password'])

        self.user.eliminate_verification_token()
        invalidate_all_user_sessions(self.user)

        return redirect(f"{reverse('accounts:login')}?info=password_changed")


class UserPasswordResetView(FormView):
    form_class = UserPasswordResetForm
    template_name = 'accounts/password_reset_form.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # not giving an info about email existence, returning fake answer
            return redirect(reverse('accounts:email_sent'))

        token = user.refresh_verification_token()
        info = extract_audit_data_from_request(self.request)

        password_reset_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:new_password_setup') + f'?token={token}'
        )

        context = {
            'password_reset_url': password_reset_url,
            'email': user.email,
            'ip_address': info['ip_address'],
            'user_agent': info['user_agent'],
            'timestamp': info['timestamp']
        }

        send_email_task.delay(
            email_type='password_reset',
            to_emails=user.email,
            context=context
        )

        return redirect(reverse('accounts:email_sent'))