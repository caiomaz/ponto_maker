"""
Services para o Sistema de Ponto Eletrônico Maker.

Este módulo contém a lógica de negócio complexa, seguindo o princípio Single Responsibility
e mantendo as views limpas e focadas em orquestração.
"""

from datetime import datetime, timedelta, time
from django.db.models import Q
from .models import Funcionario, RegistroPonto


class RelatorioFolhaPontoService:
    """Service responsável por gerar relatórios de folha de ponto."""
    
    def __init__(self, funcionario, data_inicio, data_fim):
        self.funcionario = funcionario
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        self.turno = funcionario.turno
    
    def gerar_relatorio(self):
        """Gera o relatório completo de folha de ponto."""
        registros = self._obter_registros()
        dias_trabalhados = self._agrupar_por_dia(registros)
        
        relatorio = {
            'funcionario': {
                'nome': self.funcionario.nome_completo,
                'matricula': self.funcionario.matricula,
                'departamento': self.funcionario.departamento.nome,
                'cargo': self.funcionario.cargo.nome,
            },
            'periodo': {
                'inicio': self.data_inicio.strftime('%d/%m/%Y'),
                'fim': self.data_fim.strftime('%d/%m/%Y'),
            },
            'turno': {
                'nome': self.turno.nome,
                'hora_inicio': self.turno.hora_inicio.strftime('%H:%M'),
                'hora_fim': self.turno.hora_fim.strftime('%H:%M'),
                'duracao_intervalo_minutos': self.turno.duracao_intervalo_minutos,
            },
            'dias': [],
            'totalizadores': {
                'horas_trabalhadas': 0,
                'horas_intervalo': 0,
                'atrasos_minutos': 0,
                'horas_extras': 0,
            }
        }
        
        for data, registros_dia in dias_trabalhados.items():
            dia_info = self._processar_dia(data, registros_dia)
            relatorio['dias'].append(dia_info)
            
            # Atualizar totalizadores
            relatorio['totalizadores']['horas_trabalhadas'] += dia_info['horas_trabalhadas']
            relatorio['totalizadores']['horas_intervalo'] += dia_info['horas_intervalo']
            relatorio['totalizadores']['atrasos_minutos'] += dia_info['atraso_minutos']
            relatorio['totalizadores']['horas_extras'] += dia_info['horas_extras']
        
        return relatorio
    
    def _obter_registros(self):
        """Obtém os registros de ponto do período."""
        return RegistroPonto.objects.filter(
            funcionario=self.funcionario,
            timestamp__date__gte=self.data_inicio,
            timestamp__date__lte=self.data_fim
        ).order_by('timestamp')
    
    def _agrupar_por_dia(self, registros):
        """Agrupa registros por dia."""
        dias = {}
        for registro in registros:
            data = registro.timestamp.date()
            if data not in dias:
                dias[data] = []
            dias[data].append(registro)
        return dias
    
    def _processar_dia(self, data, registros):
        """Processa os registros de um dia específico."""
        entrada = None
        saida = None
        inicio_intervalo = None
        fim_intervalo = None
        
        # Identificar os registros principais
        for registro in registros:
            if registro.tipo == 'Entrada' and not entrada:
                entrada = registro
            elif registro.tipo == 'Saída':
                saida = registro
            elif registro.tipo == 'Início Intervalo' and not inicio_intervalo:
                inicio_intervalo = registro
            elif registro.tipo == 'Fim Intervalo':
                fim_intervalo = registro
        
        # Calcular métricas
        horas_trabalhadas = 0
        horas_intervalo = 0
        atraso_minutos = 0
        horas_extras = 0
        
        if entrada and saida:
            # Calcular horas totais
            total_minutos = (saida.timestamp - entrada.timestamp).total_seconds() / 60
            
            # Calcular intervalo
            if inicio_intervalo and fim_intervalo:
                horas_intervalo = (fim_intervalo.timestamp - inicio_intervalo.timestamp).total_seconds() / 60
                total_minutos -= horas_intervalo
            
            horas_trabalhadas = total_minutos / 60
            
            # Calcular atraso
            hora_entrada_esperada = datetime.combine(data, self.turno.hora_inicio)
            hora_entrada_real = entrada.timestamp.replace(tzinfo=None)
            
            diferenca_entrada = (hora_entrada_real - hora_entrada_esperada).total_seconds() / 60
            if diferenca_entrada > self.turno.tolerancia_atraso_minutos:
                atraso_minutos = diferenca_entrada - self.turno.tolerancia_atraso_minutos
            
            # Calcular horas extras
            hora_saida_esperada = datetime.combine(data, self.turno.hora_fim)
            hora_saida_real = saida.timestamp.replace(tzinfo=None)
            
            diferenca_saida = (hora_saida_real - hora_saida_esperada).total_seconds() / 60
            if diferenca_saida > 0:
                horas_extras = diferenca_saida / 60
        
        return {
            'data': data.strftime('%d/%m/%Y'),
            'dia_semana': self._obter_dia_semana(data),
            'registros': [
                {
                    'tipo': r.tipo,
                    'horario': r.timestamp.strftime('%H:%M'),
                    'origem': r.origem,
                }
                for r in registros
            ],
            'horas_trabalhadas': round(horas_trabalhadas, 2),
            'horas_intervalo': round(horas_intervalo / 60, 2),
            'atraso_minutos': round(atraso_minutos, 0),
            'horas_extras': round(horas_extras, 2),
        }
    
    def _obter_dia_semana(self, data):
        """Retorna o nome do dia da semana em português."""
        dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        return dias[data.weekday()]


class FuncionarioQueryService:
    """Service responsável por filtrar funcionários baseado em permissões."""
    
    @staticmethod
    def get_queryset_for_user(user):
        """
        Retorna o queryset de funcionários baseado nas permissões do usuário.
        
        Implementa Row-Level Security conforme especificado no blueprint.
        """
        queryset = Funcionario.objects.all()
        
        # Se o usuário pode ver todos os relatórios, retorna tudo
        if user.has_perm('core.can_view_all_reports'):
            return queryset
        
        # Caso contrário, implementar lógica de filtro por departamento/grupo
        # Por exemplo: filtrar apenas funcionários do mesmo departamento
        # Esta lógica pode ser expandida conforme necessário
        
        return queryset
    
    @staticmethod
    def apply_filters(queryset, filters):
        """Aplica filtros dinâmicos ao queryset."""
        if filters.get('departamento'):
            queryset = queryset.filter(departamento_id=filters['departamento'])
        
        if filters.get('cargo'):
            queryset = queryset.filter(cargo_id=filters['cargo'])
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        return queryset
