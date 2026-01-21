from django import forms

from core.models import Product, ProductImage, Category, DeliverySettings


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'position', 'is_primary']
        labels = {
            'is_primary': 'Primary',
        }
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'readonly': True,
                'class': 'form-control',
                'placeholder': 'Auto-generated alternative text'
            }),
        }


ProductImageFormSet = forms.inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=1,
    can_delete=True,
    max_num=9,
    validate_max=True
)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'quantity', 'category', 'description', 'is_active']
        labels = {
            'description': 'Desc',
            'is_active': 'Visible',
        }
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Add details (optional)',
                'rows': 1,
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        qs = Product.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'Product "{name}" already exists')
        return name

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError('Price must be greater than zero')
        return price


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'description': 'Desc',
        }
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Add details (optional)',
                'rows': 2,
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        qs = Category.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'Category "{name}" already exists')
        return name


class DeliverySettingsForm(forms.ModelForm):
    class Meta:
        model = DeliverySettings
        fields = ['delivery_threshold', 'delivery_price']
        widgets = {
            'delivery_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_price': forms.NumberInput(attrs={'class': 'form-control'})
        }

    def clean_delivery_threshold(self):
        delivery_threshold = self.cleaned_data.get('delivery_threshold')
        if delivery_threshold <= 0:
            raise forms.ValidationError('Free delivery threshold must be greater than zero')
        return delivery_threshold

    def clean_delivery_price(self):
        delivery_price = self.cleaned_data.get('delivery_price')
        if delivery_price <= 0:
            raise forms.ValidationError('Delivery price must be greater than zero')
        return delivery_price