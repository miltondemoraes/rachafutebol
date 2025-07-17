from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date

class Votante(AbstractUser):
    """Modelo para os votantes (usuários que dão notas)"""
    nome_completo = models.CharField(max_length=100)
    
    # Remover campos não necessários
    first_name = None
    last_name = None
    # email = None  # Manter email para superuser
    
    def __str__(self):
        return self.nome_completo
    
    def ja_votou_hoje(self):
        """Verifica se o votante já votou hoje"""
        hoje = timezone.now().date()
        return Avaliacao.objects.filter(
            avaliador=self,
            data_avaliacao__date=hoje
        ).exists()
    
    def votou_em_todos_jogadores_hoje(self):
        """Verifica se o votante já votou em todos os jogadores hoje"""
        hoje = timezone.now().date()
        total_jogadores = Jogador.objects.filter(ativo=True).count()
        votos_hoje = Avaliacao.objects.filter(
            avaliador=self,
            data_avaliacao__date=hoje
        ).count()
        return votos_hoje >= total_jogadores

class Jogador(models.Model):
    """Modelo para os jogadores (cadastrados pelo admin)"""
    nome = models.CharField(max_length=100, unique=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome
    
    @property
    def media_avaliacoes(self):
        """Calcula a média das avaliações recebidas"""
        avaliacoes = self.avaliacoes_recebidas.all()
        if not avaliacoes:
            return 0
        return sum(a.nota for a in avaliacoes) / len(avaliacoes)
    
    @property
    def total_votos(self):
        """Retorna o total de votos recebidos"""
        return self.avaliacoes_recebidas.count()

class Avaliacao(models.Model):
    """Modelo para as avaliações (notas dos votantes para os jogadores)"""
    avaliador = models.ForeignKey(Votante, on_delete=models.CASCADE, related_name='avaliacoes_feitas')
    jogador = models.ForeignKey(Jogador, on_delete=models.CASCADE, related_name='avaliacoes_recebidas')
    nota = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('avaliador', 'jogador')
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'

    def __str__(self):
        return f"{self.avaliador.nome_completo} -> {self.jogador.nome}: {self.nota}"