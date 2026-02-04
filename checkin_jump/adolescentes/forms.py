from django import forms
from .models import Adolescente, DiaEvento, ContagemAuditorio, ContagemVisitantes
from django.core.exceptions import ValidationError
from datetime import datetime, date

class AdolescenteForm(forms.ModelForm):
    class Meta:
        model = Adolescente
        # Excluir campo 'ano' pois é preenchido automaticamente pela view
        exclude = ['ano']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome'
            }),
            'sobrenome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sobrenome'
            }),
            'data_nascimento': forms.TextInput(attrs={
                'class': 'form-control mascara-data',
                'placeholder': 'dd/mm/aaaa'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-select'
            }),
            'pg': forms.Select(attrs={
                'class': 'form-select'
            }),
            'imperio': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nome_responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo'
            }),
            'telefone_responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
        }
        labels = {
            'nome': 'Nome',
            'sobrenome': 'Sobrenome',
            'foto': 'Foto',
            'data_nascimento': 'Data de Nascimento',
            'telefone': 'Telefone',
            'genero': 'Sexo',
            'pg': 'PG',
            'imperio': 'Império',
            'nome_responsavel': 'Responsável',
            'telefone_responsavel': 'Telefone do Responsável',
        }
        help_texts = {
            'nome': '',
            'sobrenome': '',
            'telefone': '',
            'nome_responsavel': '',
            'telefone_responsavel': '',
        }
    
    def __init__(self, *args, **kwargs):
        # Otimização: receber querysets pré-carregados para evitar queries N+1
        pgs_queryset = kwargs.pop('pgs_queryset', None)
        imperios_queryset = kwargs.pop('imperios_queryset', None)
        ano = kwargs.pop('ano', None)  # Ano para filtrar PGs e Impérios
        
        super().__init__(*args, **kwargs)
        
        # Usar querysets otimizados se fornecidos, ou filtrar por ano
        if pgs_queryset is not None:
            self.fields['pg'].queryset = pgs_queryset
        elif ano:
            from .models import PequenoGrupo
            self.fields['pg'].queryset = PequenoGrupo.objects.filter(ano=ano)
        
        if imperios_queryset is not None:
            self.fields['imperio'].queryset = imperios_queryset
        elif ano:
            from .models import Imperio
            self.fields['imperio'].queryset = Imperio.objects.filter(ano=ano)

    # não permite que a data de nascimento seja no futuro
    def clean_data_nascimento(self):
        data_nascimento = self.cleaned_data.get('data_nascimento')
        if data_nascimento and data_nascimento > datetime.now().date():
            raise ValidationError("A data de nascimento não pode ser no futuro.")
        return data_nascimento


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


class ContagemVisitantesForm(forms.ModelForm):
    class Meta:
        model = ContagemVisitantes
        fields = ['dia', 'quantidade_visitantes']
        widgets = {
            'dia': forms.Select(attrs={'class': 'form-control'}),
            'quantidade_visitantes': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Ex: 35'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dia'].queryset = DiaEvento.objects.all().order_by('-data')
    
    def clean_quantidade_visitantes(self):
        quantidade = self.cleaned_data['quantidade_visitantes']
        if quantidade <= 0:
            raise forms.ValidationError("A quantidade deve ser maior que zero.")
        return quantidade
