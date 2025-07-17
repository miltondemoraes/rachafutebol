from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg
from django.db import IntegrityError
from .models import Jogador, Avaliacao
from .forms import CadastroJogadorForm, LoginForm, AvaliacaoForm
from itertools import zip_longest
import random

class TimeComMedia:
    """Classe auxiliar para representar um time com sua média"""
    def __init__(self, jogadores, media):
        self.jogadores = jogadores
        self.media_time = media
    
    def __iter__(self):
        return iter(self.jogadores)
    
    def __len__(self):
        return len(self.jogadores)

def home(request):
    """View para a página inicial - redireciona baseado no status de autenticação"""
    if request.user.is_authenticated:
        # Se for superuser, vai para admin ou lista_jogadores  
        if request.user.is_superuser:
            return redirect('lista_jogadores')
        else:
            return redirect('lista_jogadores')
    else:
        return redirect('cadastro')

def cadastro(request):
    if request.user.is_authenticated:
        return redirect('lista_jogadores')
    
    if request.method == 'POST':
        form = CadastroJogadorForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                return redirect('lista_jogadores')
            except IntegrityError:
                # CPF já existe no banco de dados
                form.add_error('cpf', 'Este CPF já está cadastrado. Tente fazer login ou use um CPF diferente.')
    else:
        form = CadastroJogadorForm()
    
    return render(request, 'cadastro.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('lista_jogadores')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('lista_jogadores')
            else:
                form.add_error(None, 'Credenciais inválidas.')
        else:
            # Debug: imprimir erros do form
            print("Erros do form:", form.errors)
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def lista_jogadores(request):
    avaliacoes_feitas = Avaliacao.objects.filter(avaliador=request.user).count()
    total_jogadores = Jogador.objects.exclude(id=request.user.id).count()
    
    if avaliacoes_feitas >= total_jogadores:
        return redirect('parcial_times')
    
    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            avaliado_id = request.POST.get('avaliado_id')
            avaliado = Jogador.objects.get(id=avaliado_id)
            
            avaliacao, created = Avaliacao.objects.get_or_create(
                avaliador=request.user,
                avaliado=avaliado,
                defaults={'nota': form.cleaned_data['nota']}
            )
            
            if not created:
                avaliacao.nota = form.cleaned_data['nota']
                avaliacao.save()
            
            return redirect('lista_jogadores')
    else:
        form = AvaliacaoForm()
    
    jogadores_nao_avaliados = Jogador.objects.exclude(
        id=request.user.id
    ).exclude(
        id__in=Avaliacao.objects.filter(avaliador=request.user).values('avaliado')
    )

    if not jogadores_nao_avaliados.exists():
        jogadores_nao_avaliados = Jogador.objects.exclude(id=request.user.id)[:1]
    
    context = {
        'jogador': jogadores_nao_avaliados.first(),
        'form': form,
        'progresso': (avaliacoes_feitas / total_jogadores) * 100 if total_jogadores > 0 else 0,
    }
    return render(request, 'lista_jogadores.html', context)

@login_required
def parcial_times(request):
    jogadores_com_media = Jogador.objects.annotate(
        media_avaliacoes=Avg('avaliacoes_recebidas__nota')
    ).exclude(media_avaliacoes__isnull=True).order_by('-media_avaliacoes')

    times_listas = distribuir_times(jogadores_com_media)
    
    # Criar estrutura de dados com média para cada time
    times_com_media = []
    for time_lista in times_listas:
        if time_lista:
            media_time = sum(j.media_avaliacoes for j in time_lista) / len(time_lista)
        else:
            media_time = 0.0
        
        times_com_media.append(TimeComMedia(time_lista, media_time))
    
    context = {
        'times': times_com_media,
        'parcial': True,
    }
    return render(request, 'times_sorteados.html', context)

@staff_member_required
def sortear_times(request):
    jogadores_com_media = Jogador.objects.annotate(
        media_avaliacoes=Avg('avaliacoes_recebidas__nota')
    ).exclude(media_avaliacoes__isnull=True).order_by('-media_avaliacoes')
    
    times_listas = distribuir_times(jogadores_com_media)
    
    # Criar estrutura de dados com média para cada time
    times_com_media = []
    for time_lista in times_listas:
        if time_lista:
            media_time = sum(j.media_avaliacoes for j in time_lista) / len(time_lista)
        else:
            media_time = 0.0
        
        times_com_media.append(TimeComMedia(time_lista, media_time))
    
    context = {
        'times': times_com_media,
        'parcial': False,
    }
    return render(request, 'times_sorteados.html', context)

def distribuir_times(jogadores):
    """
    Distribui jogadores em 4 times de 6 jogadores cada
    Usa algoritmo para equilibrar as médias dos times
    """
    lista_jogadores = list(jogadores)
    
    # Se não tiver jogadores suficientes, retorna times vazios
    if len(lista_jogadores) < 4:
        return [[], [], [], []]
    
    # Ordena por média decrescente
    lista_jogadores.sort(key=lambda x: x.media_avaliacoes, reverse=True)
    
    # Inicializa 4 times vazios
    times = [[], [], [], []]
    
    # Distribui os jogadores usando o método "serpentina" para equilibrar
    # Time 0: 1º, 8º, 9º, 16º, 17º, 24º
    # Time 1: 2º, 7º, 10º, 15º, 18º, 23º  
    # Time 2: 3º, 6º, 11º, 14º, 19º, 22º
    # Time 3: 4º, 5º, 12º, 13º, 20º, 21º
    
    for i, jogador in enumerate(lista_jogadores):
        if i < 4:
            # Primeira rodada: distribui 1 por time
            times[i].append(jogador)
        elif i < 8:
            # Segunda rodada: distribui em ordem reversa
            times[7-i].append(jogador)
        elif i < 12:
            # Terceira rodada: ordem normal novamente
            times[i-8].append(jogador)
        elif i < 16:
            # Quarta rodada: ordem reversa
            times[15-i].append(jogador)
        elif i < 20:
            # Quinta rodada: ordem normal
            times[i-16].append(jogador)
        elif i < 24:
            # Sexta rodada: ordem reversa
            times[23-i].append(jogador)
    
    # Se sobrar jogadores (mais de 24), distribui nos primeiros times
    for i in range(24, len(lista_jogadores)):
        times[i % 4].append(lista_jogadores[i])
    
    return times