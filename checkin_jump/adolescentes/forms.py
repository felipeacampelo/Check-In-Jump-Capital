from django import forms
from .models import Adolescente, DiaEvento, ContagemAuditorio
from django.core.exceptions import ValidationError
from datetime import datetime

class AdolescenteForm(forms.ModelForm):
    class Meta:
        model = Adolescente
        fields = '__all__'
        widgets = {
            'data_nascimento': forms.TextInput(attrs={
                'class': 'mascara-data',
                'placeholder': 'dd/mm/aaaa'
            }),
            'data_inicio': forms.TextInput(attrs={
                'class': 'mascara-data',
                'placeholder': 'dd/mm/aaaa'
            }),
        }

    # não permite que a data de nascimento seja no futuro
    def clean_data_nascimento(self):
        data_nascimento = self.cleaned_data.get('data_nascimento')
        if data_nascimento and data_nascimento > datetime.now().date():
            raise ValidationError("A data de nascimento não pode ser no futuro.")
        return data_nascimento

    # não permite que a data de início seja no futuro
    def clean_data_inicio(self):
        data_inicio = self.cleaned_data.get('data_inicio')
        if data_inicio and data_inicio > datetime.now().date():
            raise ValidationError("A data de início não pode ser no futuro.")
        return data_inicio


class DiaEventoForm(forms.ModelForm):
    class Meta:
        model = DiaEvento
        fields = ['data', 'titulo']
        widgets = {
            'data': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 40 Dias de Generosidade'
            })
        }

    def clean_data(self):
        data = self.cleaned_data.get('data')
        if data and data < datetime.now().date():
            raise ValidationError("Não é possível adicionar um dia no passado.")
        return data


class ContagemAuditorioForm(forms.ModelForm):
    class Meta:
        model = ContagemAuditorio
        fields = ['dia', 'quantidade_pessoas']
        widgets = {
            'dia': forms.Select(attrs={'class': 'form-control'}),
            'quantidade_pessoas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Ex: 190'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar os dias por data mais recente
        self.fields['dia'].queryset = DiaEvento.objects.all().order_by('-data')
    
    def clean_quantidade_pessoas(self):
        quantidade = self.cleaned_data['quantidade_pessoas']
        if quantidade <= 0:
            raise forms.ValidationError("A quantidade deve ser maior que zero.")
        return quantidade

