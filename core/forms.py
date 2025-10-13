from django import forms
from .models import Perfil, RegistroConsumo

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['rut', 'nombres', 'apellidos', 'tipo_vivienda']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RegistroConsumoForm(forms.ModelForm):
    class Meta:
        model = RegistroConsumo
        fields = ['fecha', 'consumo_kwh', 'costo_clp', 'dispositivo', 'fuente']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'consumo_kwh': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo_clp': forms.NumberInput(attrs={'class': 'form-control'}),
            'dispositivo': forms.Select(attrs={'class': 'form-control'}),
            'fuente': forms.TextInput(attrs={'class': 'form-control'}),
        }
