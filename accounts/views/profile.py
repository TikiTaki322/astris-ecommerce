from django.views.generic.edit import View, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.utils.dateparse import parse_date

from shared.permissions.mixins import AuthRequiredMixin, StaffOrSellerRequiredMixin
from shared.permissions.utils import is_authenticated, is_staff_or_seller

from accounts.models import UserLoginHistory, ShippingInfo
from accounts.forms import ShippingInfoForm


class UserProfileView(AuthRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if hasattr(user.customer_profile, 'shipping_info'):
            context['shipping_info'] = user.customer_profile.shipping_info
        return context


class SellerDashboardView(StaffOrSellerRequiredMixin, TemplateView):
    template_name = 'accounts/seller_dashboard.html'


class UserLoginLogsListView(AuthRequiredMixin, ListView):
    template_name = 'accounts/login_logs_list.html'
    context_object_name = 'login_logs'

    def get_queryset(self):
        qs = UserLoginHistory.objects.all()

        user = self.request.user
        if not is_staff_or_seller(self.request):
            qs = qs.filter(user=user)

        date_str = self.request.GET.get('date')
        if date_str:
            date = parse_date(date_str)
            if date:
                qs = qs.filter(timestamp__date=date)

        return qs.order_by('-timestamp')


class ShippingInfoGenericView(AuthRequiredMixin, View):
    form_class = ShippingInfoForm
    template_name = 'accounts/shipping_form.html'
    success_url = reverse_lazy('payments:review_order')

    def get(self, request):
        try:
            shipping = request.user.customer_profile.shipping_info
            form = self.form_class(instance=shipping)
        except ShippingInfo.DoesNotExist:
            form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        user = request.user
        try:
            shipping = user.customer_profile.shipping_info
            form = self.form_class(request.POST, instance=shipping)
        except ShippingInfo.DoesNotExist:
            form = self.form_class(request.POST)

        if form.is_valid():
            shipping_info = form.save(commit=False)
            shipping_info.user = user.customer_profile
            shipping_info.email = user.email
            shipping_info.save()

            next_url = self.request.GET.get('next') or self.request.POST.get('next')
            return redirect(next_url if next_url else self.success_url)

        return render(request, self.template_name, {'form': form})