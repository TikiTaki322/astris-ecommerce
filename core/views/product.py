from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.views import View

from core.forms import ProductForm, CategoryForm
from core.models import Product, Category

from shared.mixins import SellerOnlyMixin


class CategoryListView(SellerOnlyMixin, ListView):
    success_url = reverse_lazy('core:category_list')
    template_name = 'core/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        qs = Category.objects.all()
        return qs.order_by('name')


class CategoryGenericView(SellerOnlyMixin, View):
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


class CategoryDeleteView(SellerOnlyMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('core:category_list')


class ProductListView(ListView):
    template_name = 'core/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        qs = Product.objects.all()

        user = self.request.user
        stock_filter = self.request.GET.get('stock_filter')

        if not (user.is_authenticated and (user.is_staff or user.role == 'seller')):
            qs = qs.filter(quantity__gt=0)

        if stock_filter == 'out_of_stock':
            qs = qs.filter(quantity=0)
        elif stock_filter == 'in_stock':
            qs = qs.filter(quantity__gt=0)

        category = self.request.GET.get('category')
        if category and Category.objects.filter(name=category).exists():
            qs = qs.filter(category__name=category)
        return qs.order_by('-price')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admin_categories = ['DEBUG Category', 'DEV Category', 'All Stock']
        all_categories = Category.objects.all()

        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.role == 'seller')):
            all_categories = all_categories.exclude(name__in=admin_categories)

        context['categories'] = all_categories
        context['stock_filter'] = self.request.GET.get('stock_filter')
        context['selected_category'] = self.request.GET.get('category')
        return context


class ProductGenericView(SellerOnlyMixin, View):
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


class ProductDeleteView(SellerOnlyMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('core:product_list')