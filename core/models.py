"""
Models para o Sistema de Ponto Eletrônico Maker.

Este módulo contém todos os modelos de dados seguindo o princípio Single Responsibility,
onde cada modelo representa uma entidade específica do domínio de negócio.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Departamento(models.Model):
    """Representa um departamento da empresa."""
    
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Departamento'
    )
    
    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Cargo(models.Model):
    """Representa um cargo dentro da empresa."""
    
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Cargo'
    )
    
    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Turno(models.Model):
    """Representa um turno de trabalho com horários e regras específicas."""
    
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Turno'
    )
    hora_inicio = models.TimeField(
        verbose_name='Horário de Início'
    )
    hora_fim = models.TimeField(
        verbose_name='Horário de Fim'
    )
    duracao_intervalo_minutos = models.PositiveIntegerField(
        verbose_name='Duração do Intervalo (minutos)',
        validators=[MinValueValidator(0)]
    )
    tolerancia_atraso_minutos = models.PositiveIntegerField(
        default=5,
        verbose_name='Tolerância de Atraso (minutos)',
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['hora_inicio']
    
    def __str__(self):
        return f"{self.nome} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fim.strftime('%H:%M')})"


class Funcionario(models.Model):
    """Representa um funcionário da empresa."""
    
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
        ('Férias', 'Férias'),
        ('Demitido', 'Demitido'),
    ]
    
    nome_completo = models.CharField(
        max_length=255,
        verbose_name='Nome Completo'
    )
    matricula = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Matrícula'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='E-mail Corporativo'
    )
    biometric_id = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='ID Biométrico'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Ativo'
    )
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name='funcionarios'
    )
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.PROTECT,
        related_name='funcionarios'
    )
    turno = models.ForeignKey(
        Turno,
        on_delete=models.PROTECT,
        related_name='funcionarios'
    )
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome_completo']
    
    def __str__(self):
        return f"{self.nome_completo} ({self.matricula})"


class RegistroPonto(models.Model):
    """Representa um registro de ponto de um funcionário."""
    
    TIPO_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Saída', 'Saída'),
        ('Início Intervalo', 'Início Intervalo'),
        ('Fim Intervalo', 'Fim Intervalo'),
    ]
    
    ORIGEM_CHOICES = [
        ('Terminal Biométrico', 'Terminal Biométrico'),
        ('Ajuste Manual', 'Ajuste Manual'),
    ]
    
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='registros_ponto'
    )
    timestamp = models.DateTimeField(
        verbose_name='Data e Hora do Registro'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )
    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default='Terminal Biométrico'
    )
    justificativa = models.TextField(
        blank=True,
        null=True,
        verbose_name='Justificativa de Ajuste'
    )
    ajustado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ajustes_feitos'
    )
    
    class Meta:
        verbose_name = 'Registro de Ponto'
        verbose_name_plural = 'Registros de Ponto'
        ordering = ['-timestamp']
        permissions = [
            ('can_adjust_ponto', 'Pode realizar ajustes manuais no ponto'),
            ('can_view_all_reports', 'Pode visualizar todos os relatórios'),
            ('can_export_data', 'Pode exportar dados e relatórios'),
        ]
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.tipo} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
