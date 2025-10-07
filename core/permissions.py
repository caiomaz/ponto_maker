"""
Permissions customizadas para o Sistema de Ponto Eletrônico Maker.

Este módulo implementa permissões granulares seguindo o princípio Open/Closed,
permitindo extensão sem modificação do código base.
"""

from rest_framework import permissions


class CanAdjustPonto(permissions.BasePermission):
    """Permissão para realizar ajustes manuais no ponto."""
    
    message = 'Você não tem permissão para realizar ajustes manuais no ponto.'
    
    def has_permission(self, request, view):
        return request.user and request.user.has_perm('core.can_adjust_ponto')


class CanViewAllReports(permissions.BasePermission):
    """Permissão para visualizar todos os relatórios."""
    
    message = 'Você não tem permissão para visualizar todos os relatórios.'
    
    def has_permission(self, request, view):
        return request.user and request.user.has_perm('core.can_view_all_reports')


class CanExportData(permissions.BasePermission):
    """Permissão para exportar dados e relatórios."""
    
    message = 'Você não tem permissão para exportar dados.'
    
    def has_permission(self, request, view):
        return request.user and request.user.has_perm('core.can_export_data')


class IsTerminalAuthenticated(permissions.BasePermission):
    """Permissão para terminais autenticados via Token."""
    
    message = 'Autenticação de terminal necessária.'
    
    def has_permission(self, request, view):
        # Verifica se está autenticado via Token
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.auth, '__class__') and 
            request.auth.__class__.__name__ == 'Token'
        )
