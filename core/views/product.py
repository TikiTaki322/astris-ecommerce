from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView

from core.forms import ProductForm, ProductImageFormSet
from core.models import Product, Category
from core.services.product_image_sync import ProductImageSyncService
from shared.permissions.mixins import BackofficeAccessRequiredMixin
from shared.permissions.utils import is_backoffice_member
from shared.utils import redirect_with_message


class ProductListView(ListView):
    template_name = 'core/product_list.html'
    context_object_name = 'products'

    ADMIN_CATEGORIES = ['DEBUG Category', 'DEV Category']

    def get_queryset(self):
        qs = Product.objects.select_related('category').prefetch_related('images')

        if not is_backoffice_member(self.request):
            qs = qs.exclude(category__name__in=self.ADMIN_CATEGORIES)
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

        all_categories = Category.objects.all()
        if not is_backoffice_member(self.request):
            all_categories = all_categories.filter(products__isnull=False).exclude(name__in=self.ADMIN_CATEGORIES).distinct()

        context['categories'] = all_categories
        context['stock_filter'] = self.request.GET.get('stock_filter') or ''
        context['is_active_filter'] = self.request.GET.get('is_active_filter') or ''
        context['selected_category'] = self.request.GET.get('category') or ''

        context['product_toggle_visibility'] = self.request.GET.get('product_toggle_visibility')
        context['product_deletion'] = self.request.GET.get('product_deletion')
        context['cart_clear_out'] = self.request.GET.get('cart_clear_out')
        context['message'] = self.request.GET.get('message')
        return context


class ProductToggleVisibilityView(BackofficeAccessRequiredMixin, View):
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
                message = f'Product "{product.name}" was hidden'
            elif not product.is_active:
                product.is_active = True
                message = f'Product "{product.name}" again visible to the buyer'

            product.save(update_fields=['is_active'])
            response = {'success': True, 'message': message}
        except Product.DoesNotExist:
            response = {'success': False, 'message': 'Product does not exist anymore'}

        return redirect_with_message(
            'core:product_list',
            filters=filters,
            product_toggle_visibility=response.get('success', None),
            message=response.get('message', None)
        )


class ProductGenericView(BackofficeAccessRequiredMixin, View):
    form_class = ProductForm
    template_name = 'core/product_form.html'
    success_url = reverse_lazy('core:product_list')

    def get_product(self, pk):
        return Product.objects.filter(pk=pk).first() if pk else None

    def get(self, request, pk=None):
        product = self.get_product(pk)
        form = self.form_class(instance=product)
        image_formset = ProductImageFormSet(instance=product)

        context = {'form': form, 'image_formset': image_formset, 'product': product}
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        product = self.get_product(pk)
        form = self.form_class(request.POST, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=product)

        if form.is_valid() and image_formset.is_valid():
            try:
                with transaction.atomic():
                    product = form.save()
                    image_formset.instance = product
                    image_formset.save()

                    ProductImageSyncService(product).sync_product_images()

                return redirect(self.success_url)
            except Exception:
                form.add_error(None, 'Product saving error, transaction has rolled back')

        context = {'form': form, 'image_formset': image_formset, 'product': product}
        return render(request, self.template_name, context)


class ProductDetailView(DetailView):
    model = Product
    template_name = 'core/product_detail.html'
    queryset = Product.objects.select_related('category').prefetch_related('images')


class ProductDeleteView(BackofficeAccessRequiredMixin, View):
    def post(self, request, pk):
        filters = {
            'category': request.POST.get('category'),
            'stock_filter': request.POST.get('stock_filter'),
            'is_active_filter': request.POST.get('is_active_filter'),
        }

        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            response = {'success': True, 'message': f'Product "{product.name}" was deleted'}
        except Product.DoesNotExist:
            response = {'success': False, 'message': 'Product does not exist anymore'}

        return redirect_with_message(
            'core:product_list',
            filters=filters,
            product_deletion=response.get('success', None),
            message=response.get('message', None)
        )