from django import forms
from .models import SolicitudPlanNovios
from apps.productos.models import Producto

class SolicitudPlanNoviosForm(forms.ModelForm):
    class Meta:
        model = SolicitudPlanNovios
        fields = ['nombres_novios', 'apellidos_novios', 'email', 'telefono', 'fecha_boda', 'ciudad', 'mensaje', 'estado', 'clave', 'saldo_acumulado', 'monto_minimo_regalo', 'productos_regalo', 'procesado', 'foto_pareja']
        widgets = {
            'nombres_novios': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos_novios': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_boda': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'clave': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Liven2026'}),
            'saldo_acumulado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'monto_minimo_regalo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'productos_regalo': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
            'procesado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'foto_pareja': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['productos_regalo'].queryset = Producto.objects.filter(activo=True).order_by('nombre')
