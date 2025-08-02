from django import forms

from .models import Product, Category


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'price', 'quantity', 'description']

    def __init__(self, *args, **kwargs):
        # for creation through CreateView - shop comes from kwargs
        self.shop = kwargs.pop('shop', None)
        super().__init__(*args, **kwargs)

        # for updating - using shop from the instance
        if not self.shop and self.instance and self.instance.pk:
            self.shop = self.instance.shop

    def clean_name(self):
        name = self.cleaned_data.get('name')
        qs = Product.objects.filter(name=name, shop=self.shop)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'Product name "{name}" already exists in your store.')
        return name

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError(f'Price must be greater than zero.')
        return price

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk:
            instance.shop = self.shop
        if commit:
            instance.save()
        return instance


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        qs = Category.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'Category "{name}" already exists in your store.')
        return name