from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Votante, Jogador, Avaliacao

class CadastroVotanteForm(UserCreationForm):
    """Formulário para cadastro de votantes"""
    nome_completo = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu nome completo'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escolha um nome de usuário'
        })
    )
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
    )
    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        })
    )
    
    class Meta:
        model = Votante
        fields = ('nome_completo', 'username', 'password1', 'password2')
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and Votante.objects.filter(username=username).exists():
            raise ValidationError('Este nome de usuário já está em uso.')
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.nome_completo = self.cleaned_data['nome_completo']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    """Formulário de login para votantes"""
    username = forms.CharField(
        label='Nome de Usuário',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu nome de usuário'
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
    )
    
    class Meta:
        model = Votante

class CadastroJogadorForm(forms.ModelForm):
    """Formulário para o admin cadastrar jogadores"""
    class Meta:
        model = Jogador
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome do jogador'
            })
        }

class AvaliacaoForm(forms.ModelForm):
    """Formulário para avaliar um jogador"""
    class Meta:
        model = Avaliacao
        fields = ('nota',)
        widgets = {
            'nota': forms.Select(
                choices=[(i, f'{i} - {"★" * i}{"☆" * (10-i)}') for i in range(11)],
                attrs={'class': 'form-control form-control-lg'}
            )
        }
        labels = {
            'nota': 'Sua nota (0-10)'
        }