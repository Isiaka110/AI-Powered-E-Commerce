from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Product, StoreSettings, VendorProfile

class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "preferred_size")
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-4 py-3 rounded-xl border-gray-200 shadow-sm focus:border-purple-500 focus:ring focus:ring-purple-200 transition-all',
                'placeholder': 'Choose a unique username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full px-4 py-3 rounded-xl border-gray-200 shadow-sm focus:border-purple-500 focus:ring focus:ring-purple-200 transition-all',
                'placeholder': 'you@example.com'
            }),
            'preferred_size': forms.Select(attrs={
                'class': 'mt-1 block w-full px-4 py-3 rounded-xl border-gray-200 shadow-sm focus:border-purple-500 focus:ring focus:ring-purple-200 bg-white transition-all'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['preferred_size'].label = "Your Ideal Fit (AI uses this)"

# --- PRODUCT MANAGEMENT ---

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'original_price', 
            'quantity', 'image', 'image_hover', 'size', 
            'category', 'is_available'
        ]
        
        # Consistent Studio UI Classes
        input_classes = 'w-full bg-gray-50 border border-gray-100 rounded-2xl px-5 py-4 text-sm font-bold focus:ring-2 focus:ring-purple-500 outline-none transition'
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': input_classes,
                'placeholder': 'e.g. Vintage Oversized Blazer'
            }),
            'description': forms.Textarea(attrs={
                'class': input_classes, 
                'rows': 3,
                'placeholder': 'Tell the story of this piece...'
            }),
            'price': forms.NumberInput(attrs={
                'class': input_classes,
                'placeholder': '0'
            }),
            'original_price': forms.NumberInput(attrs={
                'class': 'w-full bg-red-50/30 border border-red-100 rounded-2xl px-5 py-4 text-sm font-black text-red-500 focus:ring-2 focus:ring-red-500 outline-none transition',
                'placeholder': 'Was (Optional)'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': input_classes,
                'min': '0'
            }),
            'size': forms.Select(attrs={'class': input_classes}),
            'category': forms.Select(attrs={'class': input_classes}),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'w-6 h-6 rounded-lg border-gray-300 text-purple-600 focus:ring-purple-500 transition cursor-pointer'
            }),
            # The template handles the visual styling for these
            'image': forms.ClearableFileInput(attrs={'class': 'text-[10px]'}),
            'image_hover': forms.ClearableFileInput(attrs={'class': 'text-[10px]'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Explicitly set optional fields to prevent validation errors
        self.fields['image_hover'].required = False
        self.fields['original_price'].required = False
        self.fields['description'].required = False

# --- STORE CUSTOMIZATION ---

class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        fields = ['store_name', 'logo']
        widgets = {
            'store_name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-50 border border-gray-100 rounded-xl px-4 py-3 text-sm font-bold focus:ring-2 focus:ring-purple-500 outline-none transition',
                'placeholder': 'Brand Name'
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'text-[10px] text-gray-500'
            }),
        }


class VendorOnboardingStepOneForm(forms.ModelForm):
    class Meta:
        model = VendorProfile
        fields = ["business_name", "contact_phone"]
        widgets = {
            'business_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-4 py-3 rounded-xl border border-gray-300 bg-white text-sm font-semibold focus:border-gray-900 focus:ring-gray-900',
                'placeholder': 'Thrift Elegance'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-4 py-3 rounded-xl border border-gray-300 bg-white text-sm font-semibold focus:border-gray-900 focus:ring-gray-900',
                'placeholder': '+234...'
            }),
        }
