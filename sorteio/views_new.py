from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count
from django.db import IntegrityError
from django.contrib import messages
from django.utils import timezone
from .models import Votante, Jogador, Avaliacao
from .forms import CadastroVotanteForm, LoginForm, CadastroJogadorForm, AvaliacaoForm
import random

def home(request):
    """View para a página inicial"""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            return redirect('votar')
    else:
        return redirect('cadastro')

def cadastro(request):
    """Cadastro de votantes"""
    if request.user.is_authenticated:
        return redirect('votar')
    
    if request.method == 'POST':
        form = CadastroVotanteForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.nome_completo}! Agora você pode votar.')
                return redirect('votar')
            except IntegrityError:
                form.add_error('username', 'Este nome de usuário já está em uso.')
    else:
        form = CadastroVotanteForm()
    
    return render(request, 'cadastro.html', {'form': form})

def login_view(request):
    """Login de votantes"""
    if request.user.is_authenticated:
        return redirect('votar')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return redirect('admin_dashboard')
                else:
                    return redirect('votar')
            else:
                form.add_error(None, 'Credenciais inválidas.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    """Logout"""
    logout(request)
    messages.info(request, 'Você foi desconectado.')
    return redirect('login')

@login_required
def votar(request):
    """Página principal de votação para votantes"""
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    
    # Verificar se já votou hoje
    if request.user.ja_votou_hoje():
        return redirect('parcial_times')
    
    # Pegar jogadores que ainda não foram avaliados pelo usuário hoje
    jogadores_avaliados_hoje = Avaliacao.objects.filter(
        avaliador=request.user,
        data_avaliacao__date=timezone.now().date()
    ).values_list('jogador_id', flat=True)
    
    jogadores_restantes = Jogador.objects.filter(
        ativo=True
    ).exclude(id__in=jogadores_avaliados_hoje).order_by('nome')
    
    # Se não há jogadores restantes, redirecionar para parcial
    if not jogadores_restantes.exists():
        return redirect('parcial_times')
    
    # Pegar o primeiro jogador para avaliar
    jogador = jogadores_restantes.first()
    
    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            avaliacao = form.save(commit=False)
            avaliacao.avaliador = request.user
            avaliacao.jogador = jogador
            avaliacao.save()
            
            messages.success(request, f'Nota {avaliacao.nota} atribuída para {jogador.nome}!')
            return redirect('votar')
    else:
        form = AvaliacaoForm()
    
    # Calcular progresso
    total_jogadores = Jogador.objects.filter(ativo=True).count()
    avaliacoes_feitas = Avaliacao.objects.filter(
        avaliador=request.user,
        data_avaliacao__date=timezone.now().date()
    ).count()
    
    progresso = (avaliacoes_feitas / total_jogadores) * 100 if total_jogadores > 0 else 0
    
    context = {
        'jogador': jogador,
        'form': form,
        'progresso': progresso,
        'avaliacoes_feitas': avaliacoes_feitas,
        'total_jogadores': total_jogadores,
        'jogadores_restantes': jogadores_restantes.count()
    }
    return render(request, 'votar.html', context)

@login_required
def parcial_times(request):
    """Mostrar parcial dos times - só para quem já votou"""
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    
    # Verificar se o usuário já votou hoje
    if not request.user.ja_votou_hoje():
        messages.warning(request, 'Você precisa votar em todos os jogadores para ver o parcial.')
        return redirect('votar')
    
    times = distribuir_times_equilibrados()
    
    context = {
        'times': times,
        'parcial': True,
    }
    return render(request, 'times_sorteados.html', context)

@staff_member_required
def admin_dashboard(request):
    """Dashboard do administrador"""
    total_jogadores = Jogador.objects.filter(ativo=True).count()
    total_votantes = Votante.objects.filter(is_superuser=False).count()
    total_votos = Avaliacao.objects.count()
    
    # Estatísticas de hoje
    hoje = timezone.now().date()
    votos_hoje = Avaliacao.objects.filter(data_avaliacao__date=hoje).count()
    votantes_ativos_hoje = Avaliacao.objects.filter(
        data_avaliacao__date=hoje
    ).values('avaliador').distinct().count()
    
    context = {
        'total_jogadores': total_jogadores,
        'total_votantes': total_votantes,
        'total_votos': total_votos,
        'votos_hoje': votos_hoje,
        'votantes_ativos_hoje': votantes_ativos_hoje,
    }
    return render(request, 'admin_dashboard.html', context)

@staff_member_required
def cadastrar_jogador(request):
    """Admin cadastra novos jogadores"""
    if request.method == 'POST':
        form = CadastroJogadorForm(request.POST)
        if form.is_valid():
            jogador = form.save()
            messages.success(request, f'Jogador {jogador.nome} cadastrado com sucesso!')
            return redirect('listar_jogadores')
    else:
        form = CadastroJogadorForm()
    
    return render(request, 'cadastrar_jogador.html', {'form': form})

@staff_member_required
def listar_jogadores(request):
    """Admin lista todos os jogadores"""
    jogadores = Jogador.objects.filter(ativo=True).annotate(
        total_votos=Count('avaliacoes_recebidas'),
        media_notas=Avg('avaliacoes_recebidas__nota')
    ).order_by('nome')
    
    context = {
        'jogadores': jogadores,
    }
    return render(request, 'listar_jogadores.html', context)

@staff_member_required
def sortear_times(request):
    """Admin visualiza times sorteados finais"""
    times = distribuir_times_equilibrados()
    
    context = {
        'times': times,
        'parcial': False,
    }
    return render(request, 'times_sorteados.html', context)

def distribuir_times_equilibrados():
    """Distribui 24 jogadores em 4 times de 6, de forma equilibrada"""
    # Pegar jogadores com suas médias
    jogadores = list(Jogador.objects.filter(ativo=True).annotate(
        media_notas=Avg('avaliacoes_recebidas__nota')
    ).order_by('-media_notas'))
    
    if len(jogadores) < 24:
        # Se não tem 24 jogadores, distribuir proporcionalmente
        times_count = 4
        por_time = len(jogadores) // times_count
        extras = len(jogadores) % times_count
    else:
        por_time = 6
        extras = 0
    
    # Criar 4 times vazios
    times = [[] for _ in range(4)]
    
    # Algoritmo de distribuição em serpentina para equilibrar
    for i, jogador in enumerate(jogadores):
        # Determinar qual time recebe o jogador
        ciclo = i // 4
        if ciclo % 2 == 0:
            # Ida: 0, 1, 2, 3
            time_index = i % 4
        else:
            # Volta: 3, 2, 1, 0
            time_index = 3 - (i % 4)
        
        times[time_index].append(jogador)
    
    # Calcular médias dos times
    times_com_media = []
    for i, time in enumerate(times):
        if time:
            media_time = sum(j.media_notas or 0 for j in time) / len(time)
        else:
            media_time = 0.0
        
        times_com_media.append(TimeComMedia(time, media_time))
    
    return times_com_media

class TimeComMedia:
    """Classe auxiliar para representar um time com sua média"""
    def __init__(self, jogadores, media):
        self.jogadores = jogadores
        self.media_time = media
    
    def __iter__(self):
        return iter(self.jogadores)
    
    def __len__(self):
        return len(self.jogadores)
