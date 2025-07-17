from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Votante, Jogador, Avaliacao

class VotanteAdmin(UserAdmin):
    list_display = ('username', 'nome_completo', 'is_superuser', 'date_joined')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('nome_completo',)}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'nome_completo', 'password1', 'password2', 'is_superuser'),
        }),
    )

class JogadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'data_cadastro', 'get_total_votos', 'get_media_avaliacoes')
    list_filter = ('ativo', 'data_cadastro')
    search_fields = ('nome',)
    ordering = ('nome',)
    
    def get_total_votos(self, obj):
        return obj.total_votos
    get_total_votos.short_description = 'Total de Votos'
    
    def get_media_avaliacoes(self, obj):
        return f"{obj.media_avaliacoes:.1f}" if obj.media_avaliacoes else "0.0"
    get_media_avaliacoes.short_description = 'Média das Avaliações'

class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('avaliador', 'jogador', 'nota', 'data_avaliacao')
    list_filter = ('nota', 'data_avaliacao')
    search_fields = ('avaliador__nome_completo', 'jogador__nome')
    ordering = ('-data_avaliacao',)

admin.site.register(Votante, VotanteAdmin)
admin.site.register(Jogador, JogadorAdmin)
admin.site.register(Avaliacao, AvaliacaoAdmin)