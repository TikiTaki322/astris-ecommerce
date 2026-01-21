from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DeleteView

from core.forms import CategoryForm
from core.models import Category
from shared.permissions.mixins import BackofficeAccessRequiredMixin


class CategoryListView(BackofficeAccessRequiredMixin, ListView):
    success_url = reverse_lazy('core:category_list')
    template_name = 'core/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        qs = Category.objects.all()
        return qs.order_by('-updated_at', 'name')


class CategoryGenericView(BackofficeAccessRequiredMixin, View):
    form_class = CategoryForm
    template_name = 'core/category_form.html'
    success_url = reverse_lazy('core:category_list')

    def get(self, request, pk=None):
        category = get_object_or_404(Category, pk=pk) if pk else None
        form = self.form_class(instance=category)

        return render(request, self.template_name, {'form': form, 'category': category})

    def post(self, request, pk=None):
        category = get_object_or_404(Category, pk=pk) if pk else None
        form = self.form_class(request.POST, instance=category)

        if form.is_valid():
            form.save()
            return redirect(self.success_url)

        return render(request, self.template_name, {'form': form, 'category': category})


class CategoryDeleteView(BackofficeAccessRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('core:category_list')