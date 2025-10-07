"""
Testes para o Sistema de Ponto Eletrônico Maker.

Este módulo contém testes unitários e de integração para garantir
a qualidade e confiabilidade do sistema.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from datetime import time, datetime, timedelta

from .models import Departamento, Cargo, Turno, Funcionario, RegistroPonto


class ModelTestCase(TestCase):
    """Testes para os modelos do sistema."""
    
    def setUp(self):
        """Configura dados de teste."""
        self.departamento = Departamento.objects.create(nome='TI')
        self.cargo = Cargo.objects.create(nome='Desenvolvedor')
        self.turno = Turno.objects.create(
            nome='Comercial',
            hora_inicio=time(9, 0),
            hora_fim=time(18, 0),
            duracao_intervalo_minutos=60,
            tolerancia_atraso_minutos=5
        )
    
    def test_criar_funcionario(self):
        """Testa criação de funcionário."""
        funcionario = Funcionario.objects.create(
            nome_completo='João Silva',
            matricula='12345',
            email='joao@example.com',
            biometric_id=1001,
            status='Ativo',
            departamento=self.departamento,
            cargo=self.cargo,
            turno=self.turno
        )
        
        self.assertEqual(funcionario.nome_completo, 'João Silva')
        self.assertEqual(funcionario.status, 'Ativo')
        self.assertEqual(str(funcionario), 'João Silva (12345)')
    
    def test_criar_registro_ponto(self):
        """Testa criação de registro de ponto."""
        funcionario = Funcionario.objects.create(
            nome_completo='Maria Santos',
            matricula='54321',
            email='maria@example.com',
            biometric_id=1002,
            departamento=self.departamento,
            cargo=self.cargo,
            turno=self.turno
        )
        
        registro = RegistroPonto.objects.create(
            funcionario=funcionario,
            timestamp=timezone.now(),
            tipo='Entrada',
            origem='Terminal Biométrico'
        )
        
        self.assertEqual(registro.tipo, 'Entrada')
        self.assertEqual(registro.origem, 'Terminal Biométrico')


class APIEndpointTestCase(APITestCase):
    """Testes para as APIs do sistema."""
    
    def setUp(self):
        """Configura ambiente de teste."""
        # Criar usuário e token
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Criar dados de teste
        self.departamento = Departamento.objects.create(nome='Financeiro')
        self.cargo = Cargo.objects.create(nome='Analista')
        self.turno = Turno.objects.create(
            nome='Noturno',
            hora_inicio=time(22, 0),
            hora_fim=time(6, 0),
            duracao_intervalo_minutos=30,
            tolerancia_atraso_minutos=10
        )
        self.funcionario = Funcionario.objects.create(
            nome_completo='Pedro Oliveira',
            matricula='99999',
            email='pedro@example.com',
            biometric_id=2001,
            status='Ativo',
            departamento=self.departamento,
            cargo=self.cargo,
            turno=self.turno
        )
    
    def test_listar_funcionarios(self):
        """Testa listagem de funcionários."""
        response = self.client.get('/api/v1/funcionarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_criar_departamento(self):
        """Testa criação de departamento."""
        data = {'nome': 'RH'}
        response = self.client.post('/api/v1/departamentos/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Departamento.objects.count(), 2)
    
    def test_registrar_ponto_terminal(self):
        """Testa registro de ponto via terminal."""
        data = {
            'biometric_id': 2001,
            'tipo': 'Entrada'
        }
        response = self.client.post('/api/v1/ponto/registrar/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RegistroPonto.objects.count(), 1)
    
    def test_sincronizar_funcionarios(self):
        """Testa sincronização de IDs biométricos."""
        response = self.client.get('/api/v1/funcionarios/sincronizar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('biometric_ids', response.data)
        self.assertEqual(len(response.data['biometric_ids']), 1)
    
    def test_filtrar_funcionarios_por_status(self):
        """Testa filtro de funcionários por status."""
        response = self.client.get('/api/v1/funcionarios/?status=Ativo')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class PermissionTestCase(APITestCase):
    """Testes para o sistema de permissões."""
    
    def setUp(self):
        """Configura usuários com diferentes permissões."""
        self.user_sem_permissao = User.objects.create_user(
            username='semper',
            password='test123'
        )
        self.token_sem_permissao = Token.objects.create(user=self.user_sem_permissao)
        
        self.user_com_permissao = User.objects.create_user(
            username='comper',
            password='test123'
        )
        # Adicionar permissões customizadas
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission
        
        content_type = ContentType.objects.get_for_model(RegistroPonto)
        permissions = Permission.objects.filter(content_type=content_type)
        for perm in permissions:
            self.user_com_permissao.user_permissions.add(perm)
        
        self.token_com_permissao = Token.objects.create(user=self.user_com_permissao)
        
        self.client = APIClient()
    
    def test_acesso_sem_autenticacao(self):
        """Testa acesso sem autenticação."""
        response = self.client.get('/api/v1/funcionarios/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_acesso_com_autenticacao(self):
        """Testa acesso com autenticação."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_sem_permissao.key}')
        response = self.client.get('/api/v1/funcionarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
