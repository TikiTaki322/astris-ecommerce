from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View

from core.forms import DeliverySettingsForm
from core.models import DeliverySettings
from shared.permissions.mixins import BackofficeAccessRequiredMixin


class DeliverySettingsDetailView(BackofficeAccessRequiredMixin, View):
    template_name = 'core/delivery_settings_detail.html'

    def get(self, request):
        settings = DeliverySettings.load()
        return render(request, self.template_name, {'settings': settings})


class DeliverySettingsUpdateView(BackofficeAccessRequiredMixin, View):
    form_class = DeliverySettingsForm
    template_name = 'core/delivery_settings_form.html'
    success_url = reverse_lazy('core:delivery_settings_detail')

    def get(self, request):
        settings = DeliverySettings.load()
        form = self.form_class(instance=settings)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        settings = DeliverySettings.load()
        form = self.form_class(request.POST, instance=settings)

        if form.is_valid():
            form.save()
            return redirect(self.success_url)

        return render(request, self.template_name, {'form': form})
