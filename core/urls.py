"""
URLs para o app core do Sistema de Ponto Eletrônico Maker.

Este módulo define as rotas da API seguindo as especificações do blueprint.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    DepartamentoViewSet, CargoViewSet, TurnoViewSet, FuncionarioViewSet,
    RegistroPontoViewSet, RegistroPontoTerminalView, SincronizarFuncionariosView,
    AjustePontoView, RelatorioFolhaPontoView
)

# Router para ViewSets
router = DefaultRouter()
router.register(r'departamentos', DepartamentoViewSet, basename='departamento')
router.register(r'cargos', CargoViewSet, basename='cargo')
router.register(r'turnos', TurnoViewSet, basename='turno')
router.register(r'funcionarios', FuncionarioViewSet, basename='funcionario')
router.register(r'registros', RegistroPontoViewSet, basename='registro-ponto')

# URLs da API
urlpatterns = [
    # API Interna - Terminal Biométrico
    path('v1/ponto/registrar/', RegistroPontoTerminalView.as_view(), name='ponto-registrar'),
    path('v1/funcionarios/sincronizar/', SincronizarFuncionariosView.as_view(), name='funcionarios-sincronizar'),
    
    # API Externa - Integrações
    path('v1/', include(router.urls)),
    path('v1/ajuste-ponto/', AjustePontoView.as_view(), name='ajuste-ponto'),
    path('v1/relatorios/folha-ponto/', RelatorioFolhaPontoView.as_view(), name='relatorio-folha-ponto'),
    
    # Autenticação JWT
    path('v1/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('v1/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
