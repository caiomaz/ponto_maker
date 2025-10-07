"""
Admin configuration para o Sistema de Ponto Eletrônico Maker.

Este módulo configura a interface de administração do Django, que é a ferramenta
principal para gerenciar grupos, permissões e dados do sistema.
"""

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Departamento, Cargo, Turno, Funcionario, RegistroPonto


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    """Admin para o modelo Departamento."""
    
    list_display = ['id', 'nome']
    search_fields = ['nome']
    ordering = ['nome']


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    """Admin para o modelo Cargo."""
    
    list_display = ['id', 'nome']
    search_fields = ['nome']
    ordering = ['nome']


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    """Admin para o modelo Turno."""
    
    list_display = [
        'id', 'nome', 'hora_inicio', 'hora_fim',
        'duracao_intervalo_minutos', 'tolerancia_atraso_minutos'
    ]
    search_fields = ['nome']
    ordering = ['hora_inicio']
    list_filter = ['hora_inicio']


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    """Admin para o modelo Funcionario."""
    
    list_display = [
        'id', 'nome_completo', 'matricula', 'email',
        'status', 'departamento', 'cargo', 'turno'
    ]
    list_filter = ['status', 'departamento', 'cargo', 'turno']
    search_fields = ['nome_completo', 'matricula', 'email']
    ordering = ['nome_completo']
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome_completo', 'matricula', 'email', 'biometric_id')
        }),
        ('Status e Estrutura Organizacional', {
            'fields': ('status', 'departamento', 'cargo', 'turno')
        }),
    )


@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    """Admin para o modelo RegistroPonto."""
    
    list_display = [
        'id', 'funcionario', 'timestamp', 'tipo',
        'origem', 'ajustado_por'
    ]
    list_filter = ['tipo', 'origem', 'timestamp']
    search_fields = [
        'funcionario__nome_completo',
        'funcionario__matricula'
    ]
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Registro', {
            'fields': ('funcionario', 'timestamp', 'tipo', 'origem')
        }),
        ('Ajuste Manual', {
            'fields': ('justificativa', 'ajustado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Automaticamente define o usuário que fez o ajuste."""
        if obj.origem == 'Ajuste Manual' and not obj.ajustado_por:
            obj.ajustado_por = request.user
        super().save_model(request, obj, form, change)


# Customização do admin de Groups para facilitar gestão de permissões
class GroupAdminCustom(admin.ModelAdmin):
    """Admin customizado para Groups com melhor visualização de permissões."""
    
    filter_horizontal = ['permissions']
    list_display = ['name']
    search_fields = ['name']


# Desregistra o Group padrão e registra o customizado
admin.site.unregister(Group)
admin.site.register(Group, GroupAdminCustom)


# Customização do site admin
admin.site.site_header = 'Sistema de Ponto Eletrônico Maker'
admin.site.site_title = 'Ponto Eletrônico'
admin.site.index_title = 'Administração do Sistema'
