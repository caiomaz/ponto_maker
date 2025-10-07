"""
Views para o Sistema de Ponto Eletrônico Maker.

Este módulo contém as views da API, seguindo o princípio de Dependency Inversion,
onde as views dependem de abstrações (services) e não de implementações concretas.
"""

import csv
import io
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from openpyxl import Workbook

from .models import Departamento, Cargo, Turno, Funcionario, RegistroPonto
from .serializers import (
    DepartamentoSerializer, CargoSerializer, TurnoSerializer,
    FuncionarioSerializer, FuncionarioListSerializer, RegistroPontoSerializer,
    RegistroPontoTerminalSerializer, AjustePontoSerializer, FuncionarioImportSerializer
)
from .permissions import (
    CanAdjustPonto, CanViewAllReports, CanExportData, IsTerminalAuthenticated
)
from .services import RelatorioFolhaPontoService, FuncionarioQueryService


class DepartamentoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de Departamentos."""
    
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanExportData])
    def export_csv(self, request):
        """Exporta departamentos para CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="departamentos.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nome'])
        
        for dept in self.get_queryset():
            writer.writerow([dept.id, dept.nome])
        
        return response


class CargoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de Cargos."""
    
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanExportData])
    def export_csv(self, request):
        """Exporta cargos para CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cargos.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nome'])
        
        for cargo in self.get_queryset():
            writer.writerow([cargo.id, cargo.nome])
        
        return response


class TurnoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de Turnos."""
    
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanExportData])
    def export_csv(self, request):
        """Exporta turnos para CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="turnos.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nome', 'Hora Início', 'Hora Fim', 'Duração Intervalo (min)', 'Tolerância Atraso (min)'])
        
        for turno in self.get_queryset():
            writer.writerow([
                turno.id, turno.nome, turno.hora_inicio, turno.hora_fim,
                turno.duracao_intervalo_minutos, turno.tolerancia_atraso_minutos
            ])
        
        return response


class FuncionarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de Funcionários."""
    
    queryset = Funcionario.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na action."""
        if self.action == 'list':
            return FuncionarioListSerializer
        return FuncionarioSerializer
    
    def get_queryset(self):
        """Aplica filtros e permissões de nível de objeto."""
        queryset = FuncionarioQueryService.get_queryset_for_user(self.request.user)
        
        # Aplicar filtros via query parameters
        filters = {
            'departamento': self.request.query_params.get('departamento'),
            'cargo': self.request.query_params.get('cargo'),
            'status': self.request.query_params.get('status'),
        }
        
        return FuncionarioQueryService.apply_filters(queryset, filters)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def import_csv(self, request):
        """Importa funcionários via CSV."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'Arquivo CSV não fornecido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        csv_file = request.FILES['file']
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            imported = []
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                serializer = FuncionarioImportSerializer(data=row)
                if serializer.is_valid():
                    funcionario = serializer.save()
                    imported.append(funcionario.matricula)
                else:
                    errors.append({
                        'linha': row_num,
                        'erros': serializer.errors
                    })
            
            return Response({
                'importados': len(imported),
                'erros': errors
            }, status=status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS)
        
        except Exception as e:
            return Response(
                {'error': f'Erro ao processar arquivo: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanExportData])
    def export_csv(self, request):
        """Exporta funcionários para CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="funcionarios.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Nome Completo', 'Matrícula', 'Email', 'ID Biométrico',
            'Status', 'Departamento', 'Cargo', 'Turno'
        ])
        
        for func in self.get_queryset():
            writer.writerow([
                func.id, func.nome_completo, func.matricula, func.email,
                func.biometric_id, func.status, func.departamento.nome,
                func.cargo.nome, func.turno.nome
            ])
        
        return response
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanExportData])
    def export_excel(self, request):
        """Exporta funcionários para Excel."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Funcionários"
        
        # Cabeçalhos
        headers = [
            'ID', 'Nome Completo', 'Matrícula', 'Email', 'ID Biométrico',
            'Status', 'Departamento', 'Cargo', 'Turno'
        ]
        ws.append(headers)
        
        # Dados
        for func in self.get_queryset():
            ws.append([
                func.id, func.nome_completo, func.matricula, func.email,
                func.biometric_id, func.status, func.departamento.nome,
                func.cargo.nome, func.turno.nome
            ])
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="funcionarios.xlsx"'
        wb.save(response)
        
        return response


class RegistroPontoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de Registros de Ponto."""
    
    queryset = RegistroPonto.objects.all()
    serializer_class = RegistroPontoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra registros baseado em permissões e parâmetros."""
        queryset = RegistroPonto.objects.all()
        
        # Filtros obrigatórios para API externa
        matricula = self.request.query_params.get('matricula_funcionario')
        data_inicio = self.request.query_params.get('data_inicio')
        data_fim = self.request.query_params.get('data_fim')
        
        if matricula:
            queryset = queryset.filter(funcionario__matricula=matricula)
        
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=data_inicio_dt)
            except ValueError:
                pass
        
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=data_fim_dt)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanExportData])
    def export_csv(self, request):
        """Exporta registros de ponto para CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="registros_ponto.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Funcionário', 'Matrícula', 'Data/Hora', 'Tipo',
            'Origem', 'Justificativa', 'Ajustado Por'
        ])
        
        for registro in self.get_queryset():
            writer.writerow([
                registro.id, registro.funcionario.nome_completo,
                registro.funcionario.matricula, registro.timestamp,
                registro.tipo, registro.origem, registro.justificativa or '',
                registro.ajustado_por.username if registro.ajustado_por else ''
            ])
        
        return response


class RegistroPontoTerminalView(generics.CreateAPIView):
    """View para registro de ponto via terminal biométrico."""
    
    serializer_class = RegistroPontoTerminalSerializer
    permission_classes = [IsAuthenticated, IsTerminalAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Processa o registro de ponto do terminal."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registro = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Ponto registrado com sucesso.',
            'registro': {
                'funcionario': registro.funcionario.nome_completo,
                'tipo': registro.tipo,
                'timestamp': registro.timestamp.strftime('%d/%m/%Y %H:%M:%S')
            }
        }, status=status.HTTP_201_CREATED)


class SincronizarFuncionariosView(generics.ListAPIView):
    """View para sincronização de IDs biométricos com o terminal."""
    
    permission_classes = [IsAuthenticated, IsTerminalAuthenticated]
    
    def list(self, request, *args, **kwargs):
        """Retorna lista de IDs biométricos ativos."""
        biometric_ids = list(
            Funcionario.objects.filter(
                status='Ativo',
                biometric_id__isnull=False
            ).values_list('biometric_id', flat=True)
        )
        
        return Response({
            'biometric_ids': biometric_ids
        }, status=status.HTTP_200_OK)


class AjustePontoView(generics.CreateAPIView):
    """View para ajustes manuais de ponto."""
    
    serializer_class = AjustePontoSerializer
    permission_classes = [IsAuthenticated, CanAdjustPonto]
    
    def create(self, request, *args, **kwargs):
        """Cria um ajuste manual de ponto."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        registro = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Ajuste de ponto realizado com sucesso.',
            'registro_id': registro.id
        }, status=status.HTTP_201_CREATED)


class RelatorioFolhaPontoView(generics.GenericAPIView):
    """View para geração de relatório de folha de ponto."""
    
    permission_classes = [IsAuthenticated, CanViewAllReports]
    
    def get(self, request, *args, **kwargs):
        """Gera relatório de folha de ponto."""
        matricula = request.query_params.get('matricula_funcionario')
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        # Validar parâmetros obrigatórios
        if not all([matricula, data_inicio, data_fim]):
            return Response({
                'error': 'Parâmetros obrigatórios: matricula_funcionario, data_inicio, data_fim'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            funcionario = Funcionario.objects.get(matricula=matricula)
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except Funcionario.DoesNotExist:
            return Response({
                'error': 'Funcionário não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({
                'error': 'Formato de data inválido. Use YYYY-MM-DD.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Gerar relatório usando o service
        service = RelatorioFolhaPontoService(funcionario, data_inicio_dt, data_fim_dt)
        relatorio = service.gerar_relatorio()
        
        return Response(relatorio, status=status.HTTP_200_OK)
