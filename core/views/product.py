from django.views.generic import ListView, DetailView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View

from core.forms import ProductForm, CategoryForm
from core.models import Product, Category

from shared.permissions.mixins import AuthRequiredMixin, StaffOrSellerRequiredMixin
from shared.permissions.utils import is_authenticated, is_staff_or_seller
from shared.utils import redirect_with_message


class CategoryListView(StaffOrSellerRequiredMixin, ListView):
    success_url = reverse_lazy('core:category_list')
    template_name = 'core/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        qs = Category.objects.all()
        return qs.order_by('-updated_at', 'name')


class CategoryGenericView(StaffOrSellerRequiredMixin, View):
    form_class = CategoryForm
    template_name = 'core/category_form.html'
    success_url = reverse_lazy('core:category_list')

    def get(self, request, pk=None):
        if pk:
            category = get_object_or_404(Category, pk=pk)
            form = self.form_class(instance=category)
        else:
            form = self.form_class()
        return render(request, self.template_name, {'form': form, 'category': category if pk else None})

    def post(self, request, pk=None):
        if pk:
            category = get_object_or_404(Category, pk=pk)
            form = self.form_class(request.POST, instance=category)
        else:
            form = self.form_class(request.POST)

        if form.is_valid():
            form.save()
            return redirect(self.success_url)

        return render(request, self.template_name, {'form': form, 'category': category if pk else None})


class CategoryDeleteView(StaffOrSellerRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('core:category_list')


class ProductListView(ListView):
    template_name = 'core/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        qs = Product.objects.all()

        if not is_staff_or_seller(self.request):
            qs = qs.filter(quantity__gt=0, is_active=True)
        else:
            stock_filter = self.request.GET.get('stock_filter')
            if stock_filter == 'out_of_stock':
                qs = qs.filter(quantity=0)
            elif stock_filter == 'in_stock':
                qs = qs.filter(quantity__gt=0)

            is_active_filter = self.request.GET.get('is_active_filter')
            if is_active_filter == 'deactivated':
                qs = qs.filter(is_active=False)

        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category__name=category)
        return qs.order_by('-updated_at', '-price')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        admin_categories = ['DEBUG Category', 'DEV Category', 'All Stock']
        all_categories = Category.objects.all()

        if not is_staff_or_seller(self.request):
            all_categories = all_categories.exclude(name__in=admin_categories)

        context['categories'] = all_categories
        context['stock_filter'] = self.request.GET.get('stock_filter') or ''
        context['is_active_filter'] = self.request.GET.get('is_active_filter') or ''
        context['selected_category'] = self.request.GET.get('category') or ''

        context['product_toggle_visibility'] = self.request.GET.get('product_toggle_visibility')
        context['product_deletion'] = self.request.GET.get('product_deletion')
        context['message'] = self.request.GET.get('message')
        return context


class ProductToggleVisibilityView(StaffOrSellerRequiredMixin, View):
    def post(self, request, pk):
        filters = {
            'category': request.POST.get('category'),
            'stock_filter': request.POST.get('stock_filter'),
            'is_active_filter': request.POST.get('is_active_filter'),
        }

        try:
            product = Product.objects.get(pk=pk)
            if product.is_active:
                product.is_active = False
                message = f'Product "{product.name}" was deactivated.'
            elif not product.is_active:
                product.is_active = True
                message = f'Product "{product.name}" was activated.'

            product.save(update_fields=['is_active', 'updated_at'])
            response = {'success': True, 'message': message}
        except Product.DoesNotExist:
            response = {'success': False, 'message': 'Product does not exist anymore.'}

        return redirect_with_message(
            'core:product_list',
            filters=filters,
            product_toggle_visibility=response.get('success', None),
            message=response.get('message', None)
        )


class ProductGenericView(StaffOrSellerRequiredMixin, View):
    form_class = ProductForm
    template_name = 'core/product_form.html'
    success_url = reverse_lazy('core:product_list')

    def get_form_kwargs(self):
        return {'shop': self.request.user.seller_profile.shop}

    def get(self, request, pk=None):
        if pk:
            product = get_object_or_404(Product, pk=pk)
            form = self.form_class(instance=product)
        else:
            form = self.form_class()
        return render(request, self.template_name, {'form': form, 'product': product if pk else None})

    def post(self, request, pk=None):
        if pk:
            product = get_object_or_404(Product, pk=pk)
            form = self.form_class(request.POST, instance=product)
        else:
            form = self.form_class(request.POST)

        if form.is_valid():
            form.shop = request.user.seller_profile.shop
            form.save()
            return redirect(self.success_url)

        return render(request, self.template_name, {'form': form, 'product': product if pk else None})


class ProductDetailView(DetailView):
    model = Product
    template_name = 'core/product_detail.html'


class ProductDeleteView(StaffOrSellerRequiredMixin, View):
    def post(self, request, pk):
        filters = {
            'category': request.POST.get('category'),
            'stock_filter': request.POST.get('stock_filter'),
            'is_active_filter': request.POST.get('is_active_filter'),
        }

        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            response = {'success': True, 'message': f'Product "{product.name}" was deleted.'}
        except Product.DoesNotExist:
            response = {'success': False, 'message': 'Product does not exist anymore.'}

        return redirect_with_message(
            'core:product_list',
            filters=filters,
            product_deletion=response.get('success', None),
            message=response.get('message', None)
        )