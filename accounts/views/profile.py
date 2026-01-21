from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import View

from accounts.forms import ShippingInfoForm
from accounts.models import UserLoginHistory
from shared.permissions.mixins import BackofficeAccessRequiredMixin, AuthRequiredMixin
from shared.permissions.utils import is_backoffice_member


class BackofficeDashboardView(BackofficeAccessRequiredMixin, TemplateView):
    template_name = 'accounts/backoffice_dashboard.html'


class CustomerAccountView(AuthRequiredMixin, TemplateView):
    template_name = 'accounts/customer_account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if hasattr(user.customer_profile, 'shipping_info'):
            context['shipping_info'] = user.customer_profile.shipping_info
        return context


class UserLoginLogsListView(AuthRequiredMixin, ListView):
    template_name = 'accounts/login_logs_list.html'
    context_object_name = 'login_logs'

    def get_queryset(self):
        qs = UserLoginHistory.objects.select_related('user')

        user = self.request.user
        if not is_backoffice_member(self.request):
            qs = qs.filter(user=user)

        date_str = self.request.GET.get('date')
        if date_str:
            date = parse_date(date_str)
            if date:
                qs = qs.filter(timestamp__date=date)

        return qs.order_by('-timestamp')


class ShippingInfoGenericView(AuthRequiredMixin, View):
    form_class = ShippingInfoForm
    template_name = 'accounts/shipping_data_form.html'
    success_url = reverse_lazy('payments:review_order')

    def get_shipping(self, user):
        if hasattr(user.customer_profile, 'shipping_info'):
            return user.customer_profile.shipping_info
        return None

    def get(self, request):
        user = request.user
        shipping = self.get_shipping(user)
        form = self.form_class(instance=shipping)

        return render(request, self.template_name, {'form': form})

    def post(self, request):
        user = request.user
        shipping = self.get_shipping(user)
        form = self.form_class(request.POST, instance=shipping)

        if form.is_valid():
            shipping_info = form.save(commit=False)
            shipping_info.user = user.customer_profile
            shipping_info.email = user.email
            shipping_info.save()

            next_url = self.request.GET.get('next') or self.request.POST.get('next')
            return redirect(next_url if next_url else self.success_url)

        return render(request, self.template_name, {'form': form})