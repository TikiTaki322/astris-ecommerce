from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from accounts.forms import UserLoginForm
from core.services.order_builder import OrderBuilderService


class UserLoginView(LoginView):
    authentication_form = UserLoginForm
    template_name = 'accounts/login_form.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if info := self.request.GET.get('info'):
            context['info'] = info
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if session_order := self.request.session.get('session_order', {}):
            OrderBuilderService(session_order=session_order, user=self.request.user).build()  # Merge session with order
            del self.request.session['session_order']
        return response


@method_decorator(csrf_protect, name='dispatch')
class UserLogoutView(LogoutView):
    next_page = reverse_lazy('core:product_list')