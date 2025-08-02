from django.contrib.auth.views import LoginView, LogoutView
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy

from core.services.order_builder import OrderBuilderService
from accounts.forms import UserLoginForm


class UserLoginView(LoginView):
    authentication_form = UserLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        info_msg = self.request.GET.get('info')
        if info_msg:
            context['info'] = info_msg
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        session_order = self.request.session.get('session_order', {})
        if session_order:
            _ = OrderBuilderService(session_order, self.request.user).build()  # Update an order based on the session
            del self.request.session['session_order']
        return response


@method_decorator(csrf_protect, name='dispatch')
class UserLogoutView(LogoutView):
    next_page = reverse_lazy('core:product_list')