from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse

from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_protect

from django.views.generic.edit import View, CreateView, UpdateView, FormView
from django.views.generic import TemplateView, ListView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm, UserPasswordCheckForm, \
    UserSetPasswordForm, UserEmailUpdateForm

from .utils import generate_email_verification_token, get_user_by_email_verification_token, link_lifetime_check, \
    invalidate_all_user_sessions

from accounts.services.email_sender import send_email_via_resend
from core.services.order_builder import OrderBuilderService

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# class UserRegisterView(FormView):
#     form_class = UserRegistrationForm
#     template_name = 'accounts/register.html'
#
#     def form_valid(self, form):
#         username = form.cleaned_data['username']
#         email = form.cleaned_data['email']
#         password = form.cleaned_data['password1']
#         email_sent_at = timezone.now().isoformat()  # datetime to str
#
#         # Email confirmation link
#         token = generate_email_verification_token()
#         verify_url = self.request.build_absolute_uri(
#             reverse_lazy('accounts:verify_email') + f'?token={token}'
#         )
#
#         html_content = render_to_string('emails/registration_request.html', {
#             'verify_url': verify_url,
#             'username': username,
#         })
#         text_content = render_to_string('emails/registration_request.txt', {
#             'verify_url': verify_url,
#             'username': username,
#         })
#
#         try:
#             # Email sending
#             send_email_via_resend(
#                 to_emails=email,
#                 subject='Confirm your registration on rawpapers.store',
#                 html_content=html_content,
#                 text_content=text_content,
#             )
#         except Exception as e:
#             logger.warning(f'Email sending failed: {email} | {e}\n\n')
#             return self.form_invalid(form)
#
#         # Temporary saving user-registration form data within session
#         self.request.session['pending_user'] = {
#             'username': username,
#             'email': email,
#             'password': password,
#             'token': token,
#             'email_sent_at': email_sent_at,
#         }
#
#         return redirect(reverse('accounts:email_sent'))


# class UserRegisterConfirmView(TemplateView):
#     template_name = 'accounts/link_error.html'
#
#     def get(self, request, *args, **kwargs):
#         token = request.GET.get('token')
#         data = request.session.get('pending_user')
#
#         if not token or not data or token != data.get('token'):
#             return self.render_to_response({'success': False, 'message': '❌ Invalid token or expired session.'})
#
#         logger.warning(f"Attempt to activate: {data['email']}")
#
#         email_sent_at = parse_datetime(data['email_sent_at'])  # str to datetime
#         if not link_lifetime_check(email_sent_at):
#             logger.warning(f"Verification link has been expired: {data['email']}\n\n")
#             # del request.session['pending_user']
#             return self.render_to_response({'success': False, 'message': '⏳ Verification link has been expired.'})
#
#         user = User(
#             username=data['username'],
#             email=data['email'],
#             email_verified=True,
#             email_verification_token=None,
#             email_sent_at=email_sent_at,
#         )
#         user.set_password(data['password'])
#         user.save()
#         logger.warning(f'Email verified: {user.email} | User created: {user.username}\n\n')
#
#         session_order = request.session.get('session_order', {})
#         if session_order:
#             _ = OrderBuilderService(session_order, user).build()  # Build an order based on the session
#             del request.session['session_order']
#         del request.session['pending_user']
#
#         return redirect(f"{reverse('accounts:login')}?success=email_verified")

#
# class UserPasswordChangeView(FormView):
#     form_class = UserPasswordCheckForm
#     template_name = 'accounts/password_change_request_validation.html'
#
#     def form_valid(self, form):
#         current = form.cleaned_data['password']
#
#         user = self.request.user
#         if not user.check_password(current):
#             form.add_error('password', 'Wrong password')
#             return self.form_invalid(form)
#
#         user.refresh_verification_token()  # creation token, timestamp and saving in DB
#         token = user.email_verification_token
#         change_password_url = self.request.build_absolute_uri(
#             reverse_lazy('accounts:confirm_password_change') + f'?token={token}'
#         )
#
#         html_content = render_to_string('emails/password_change_request.html', {
#             'change_password_url': change_password_url,
#             'username': user.username,
#         })
#
#         text_content = render_to_string('emails/password_change_request.txt', {
#             'change_password_url': change_password_url,
#             'username': user.username,
#         })
#
#         try:
#             send_email_via_resend(
#                 to_emails=user.email,
#                 subject='Changing password on rawpapers.store',
#                 html_content=html_content,
#                 text_content=text_content,
#             )
#         except Exception as e:
#             logger.warning(f'Email sending failed: {user.email} | {e}\n\n')
#             return self.form_invalid(form)
#
#         return redirect(reverse('accounts:email_sent'))
#
#
# class UserPasswordChangeConfirmView(FormView):
#     form_class = UserSetPasswordForm
#     template_name = 'accounts/password_change_request_processing.html'
#
#     def dispatch(self, request, *args, **kwargs):
#         token = request.GET.get('token')
#         self.user = get_user_by_email_verification_token(token)
#         self.invalid_token = not self.user or not link_lifetime_check(self.user.email_sent_at)
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         if getattr(self, 'invalid_token', False):
#             context.update({'success': False, 'message': '⏳ The link has been expired.'})
#         else:
#             context.update({'success': True})
#
#         return context
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['user'] = self.user  # necessarily for SetPasswordForm
#         return kwargs
#
#     def form_valid(self, form):
#         new_password = form.cleaned_data['new_password1']
#         if self.user.check_password(new_password):
#             form.add_error('new_password1', 'The new password cannot be the same as the old one.')
#             return self.form_invalid(form)
#
#         form.save()
#         self.user.email_verification_token = None
#         self.user.save()
#         invalidate_all_user_sessions(self.user)
#
#         info = self.user.last_login_info
#         ip_address = info['ip_address']
#         user_agent = info['user_agent']
#         timestamp = info['timestamp']
#
#         html_content = render_to_string('emails/password_changed_notification.html', {
#             'username': self.user.username,
#             'ip_address': ip_address,
#             'user_agent': user_agent,
#             'timestamp': timestamp
#         })
#
#         text_content = render_to_string('emails/password_changed_notification.txt', {
#             'username': self.user.username,
#             'ip_address': ip_address,
#             'user_agent': user_agent,
#             'timestamp': timestamp
#         })
#
#         try:
#             send_email_via_resend(
#                 to_emails=self.user.email,
#                 subject='Password changed on rawpapers.store',
#                 html_content=html_content,
#                 text_content=text_content,
#             )
#         except Exception as e:
#             logger.warning(f'Email sending failed: {self.user.email} | {e}\n\n')
#             return self.form_invalid(form)
#
#         return redirect(f"{reverse('accounts:login')}?success=password_changed")

#
# class UserEmailUpdateView(FormView):
#     form_class = UserEmailUpdateForm
#     template_name = 'accounts/email_change_request.html'
#
#     def form_valid(self, form):
#         new_email = form.cleaned_data['new_email']
#         current = form.cleaned_data['password']
#         user = self.request.user
#
#         if not user.check_password(current):
#             form.add_error('password', 'Wrong password')
#             return self.form_invalid(form)
#
#         user.refresh_verification_token()  # creation token, timestamp and saving in DB
#         token = user.email_verification_token
#         change_email_url = self.request.build_absolute_uri(
#             reverse_lazy('accounts:confirm_email_update') + f'?token={token}&new_email={new_email}'
#         )
#
#         info = user.last_login_info
#         ip_address = info['ip_address']
#         user_agent = info['user_agent']
#         timestamp = info['timestamp']
#
#         html_content = render_to_string('emails/email_reassign_initiating.html', {
#             'change_email_url': change_email_url,
#             'username': user.username,
#             'ip_address': ip_address,
#             'user_agent': user_agent,
#             'timestamp': timestamp
#         })
#
#         text_content = render_to_string('emails/email_reassign_initiating.txt', {
#             'change_email_url': change_email_url,
#             'username': user.username,
#             'ip_address': ip_address,
#             'user_agent': user_agent,
#             'timestamp': timestamp
#         })
#
#         try:
#             send_email_via_resend(
#                 to_emails=new_email,
#                 subject='Mail reassignment on rawpapers.store',
#                 html_content=html_content,
#                 text_content=text_content,
#             )
#         except Exception as e:
#             logger.warning(f'Email sending failed: {new_email} | {e}\n\n')
#             return self.form_invalid(form)
#
#         return redirect(reverse('accounts:email_sent'))
#
#
# class UserEmailUpdateConfirmView(TemplateView):
#     template_name = 'accounts/link_error.html'
#
#     def get(self, request, *args, **kwargs):
#         token = request.GET.get('token')
#         new_email = request.GET.get('new_email')
#         if not token or not new_email:
#             return self.render_to_response({'success': False, 'message': '❌ Invalid request.'})
#
#         user = get_user_by_email_verification_token(token)
#         if not user or not link_lifetime_check(user.email_sent_at):
#             return self.render_to_response({'success': False, 'message': '⏳ Verification link has been expired.'})
#
#         old_email = user.email
#         user.email = new_email
#         user.email_verification_token = None
#         user.save()
#         invalidate_all_user_sessions(user)
#
#         info = user.last_login_info
#         ip_address = info['ip_address']
#         user_agent = info['user_agent']
#         timestamp = info['timestamp']
#
#         html_content = render_to_string('emails/email_reassigned_notification.html', {
#             'username': user.username,
#             'ip_address': ip_address,
#             'user_agent': user_agent,
#             'timestamp': timestamp
#         })
#
#         text_content = render_to_string('emails/email_reassigned_notification.txt', {
#             'username': user.username,
#             'ip_address': ip_address,
#             'user_agent': user_agent,
#             'timestamp': timestamp
#         })
#
#         try:
#             send_email_via_resend(
#                 to_emails=[old_email, new_email],
#                 subject='Mail reassigned on rawpapers.store',
#                 html_content=html_content,
#                 text_content=text_content,
#             )
#         except Exception as e:
#             logger.warning(f'Email sending failed: {[old_email, new_email]} | {e}\n\n')
#
#         return redirect(f"{reverse('accounts:login')}?success=email_changed")


# class UserShippingUpdateView(View):
#     pass


# class UserLoginView(LoginView):
#     authentication_form = UserLoginForm
#     template_name = 'accounts/login.html'
#     redirect_authenticated_user = True
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         success_msg = self.request.GET.get('success')
#         if success_msg:
#             context['success'] = success_msg
#         return context
#
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         session_order = self.request.session.get('session_order', {})
#         if session_order:
#             _ = OrderBuilderService(session_order, self.request.user).build()  # Update an order based on the session
#             del self.request.session['session_order']
#         return response


# @method_decorator(csrf_protect, name='dispatch')
# class UserLogoutView(LogoutView):
#     next_page = reverse_lazy('core:product_list')


# class UserProfileView(TemplateView):
#     template_name = 'accounts/profile.html'


# class UserProfileUpdateView(UpdateView):
#     model = User
#     form_class = UserProfileUpdateForm
#     template_name = 'accounts/profile_update_INVALID_DELETE_LATER!.html'
#     success_url = reverse_lazy('accounts:profile')
#
#     def get_object(self, queryset=None):  # method removes the need for pk in the URL. Such approach gives more security
#         return self.request.user
#
#     def form_invalid(self, form):
#         self.object.refresh_from_db()
#         return super().form_invalid(form)
#
#
# class UserLoginLogsListView(ListView):
#     template_name = 'accounts/login_logs_list.html'
#     context_object_name = 'login_logs'
#
#     def get_queryset(self):
#         return self.request.user.login_logs
