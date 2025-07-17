from django.urls import path
from . import views

urlpatterns = [
    # Páginas públicas
    path('', views.home, name='home'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Páginas para votantes
    path('votar/', views.votar, name='votar'),
    path('parcial/', views.parcial_times, name='parcial_times'),
    
    # Páginas para admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('cadastrar-jogador/', views.cadastrar_jogador, name='cadastrar_jogador'),
    path('listar-jogadores/', views.listar_jogadores, name='listar_jogadores'),
    path('sortear-times/', views.sortear_times, name='sortear_times'),
]