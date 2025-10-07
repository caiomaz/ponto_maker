"""
Serializers para o Sistema de Ponto Eletrônico Maker.

Este módulo contém os serializers do DRF, seguindo o princípio de Interface Segregation,
onde cada serializer tem uma responsabilidade específica e clara.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Departamento, Cargo, Turno, Funcionario, RegistroPonto


class DepartamentoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Departamento."""
    
    class Meta:
        model = Departamento
        fields = ['id', 'nome']


class CargoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Cargo."""
    
    class Meta:
        model = Cargo
        fields = ['id', 'nome']


class TurnoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Turno."""
    
    class Meta:
        model = Turno
        fields = [
            'id', 'nome', 'hora_inicio', 'hora_fim',
            'duracao_intervalo_minutos', 'tolerancia_atraso_minutos'
        ]


class FuncionarioSerializer(serializers.ModelSerializer):
    """Serializer completo para o modelo Funcionario."""
    
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    cargo_nome = serializers.CharField(source='cargo.nome', read_only=True)
    turno_nome = serializers.CharField(source='turno.nome', read_only=True)
    
    class Meta:
        model = Funcionario
        fields = [
            'id', 'nome_completo', 'matricula', 'email', 'biometric_id',
            'status', 'departamento', 'departamento_nome', 'cargo',
            'cargo_nome', 'turno', 'turno_nome'
        ]
        read_only_fields = ['id']


class FuncionarioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de funcionários."""
    
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    cargo_nome = serializers.CharField(source='cargo.nome', read_only=True)
    
    class Meta:
        model = Funcionario
        fields = [
            'id', 'nome_completo', 'matricula', 'email',
            'status', 'departamento_nome', 'cargo_nome'
        ]


class RegistroPontoSerializer(serializers.ModelSerializer):
    """Serializer completo para o modelo RegistroPonto."""
    
    funcionario_nome = serializers.CharField(source='funcionario.nome_completo', read_only=True)
    ajustado_por_username = serializers.CharField(source='ajustado_por.username', read_only=True)
    
    class Meta:
        model = RegistroPonto
        fields = [
            'id', 'funcionario', 'funcionario_nome', 'timestamp', 'tipo',
            'origem', 'justificativa', 'ajustado_por', 'ajustado_por_username'
        ]
        read_only_fields = ['id', 'ajustado_por']
    
    def validate(self, data):
        """Valida que ajustes manuais devem ter justificativa."""
        if data.get('origem') == 'Ajuste Manual' and not data.get('justificativa'):
            raise serializers.ValidationError({
                'justificativa': 'Justificativa é obrigatória para ajustes manuais.'
            })
        return data


class RegistroPontoTerminalSerializer(serializers.Serializer):
    """Serializer para registro de ponto via terminal biométrico."""
    
    biometric_id = serializers.IntegerField(required=True)
    tipo = serializers.ChoiceField(
        choices=['Entrada', 'Saída', 'Início Intervalo', 'Fim Intervalo'],
        required=True
    )
    
    def validate_biometric_id(self, value):
        """Valida se o biometric_id existe e está ativo."""
        try:
            funcionario = Funcionario.objects.get(biometric_id=value)
            if funcionario.status != 'Ativo':
                raise serializers.ValidationError(
                    f'Funcionário com status "{funcionario.status}" não pode registrar ponto.'
                )
        except Funcionario.DoesNotExist:
            raise serializers.ValidationError('ID biométrico não encontrado.')
        return value
    
    def create(self, validated_data):
        """Cria um novo registro de ponto via terminal."""
        funcionario = Funcionario.objects.get(biometric_id=validated_data['biometric_id'])
        registro = RegistroPonto.objects.create(
            funcionario=funcionario,
            timestamp=timezone.now(),
            tipo=validated_data['tipo'],
            origem='Terminal Biométrico'
        )
        return registro


class AjustePontoSerializer(serializers.ModelSerializer):
    """Serializer específico para ajustes manuais de ponto."""
    
    class Meta:
        model = RegistroPonto
        fields = ['id', 'funcionario', 'timestamp', 'tipo', 'justificativa']
    
    def validate_justificativa(self, value):
        """Garante que a justificativa não está vazia."""
        if not value or not value.strip():
            raise serializers.ValidationError('Justificativa é obrigatória para ajustes manuais.')
        return value
    
    def create(self, validated_data):
        """Cria um ajuste manual de ponto."""
        validated_data['origem'] = 'Ajuste Manual'
        validated_data['ajustado_por'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Atualiza um registro de ponto existente."""
        instance.origem = 'Ajuste Manual'
        instance.ajustado_por = self.context['request'].user
        return super().update(instance, validated_data)


class FuncionarioImportSerializer(serializers.Serializer):
    """Serializer para importação de funcionários via CSV."""
    
    nome_completo = serializers.CharField(max_length=255)
    matricula = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    biometric_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['Ativo', 'Inativo', 'Férias', 'Demitido'],
        default='Ativo'
    )
    departamento_nome = serializers.CharField(max_length=100)
    cargo_nome = serializers.CharField(max_length=100)
    turno_nome = serializers.CharField(max_length=100)
    
    def validate(self, data):
        """Valida e busca as relações necessárias."""
        # Buscar ou criar departamento
        departamento, _ = Departamento.objects.get_or_create(nome=data['departamento_nome'])
        data['departamento'] = departamento
        
        # Buscar ou criar cargo
        cargo, _ = Cargo.objects.get_or_create(nome=data['cargo_nome'])
        data['cargo'] = cargo
        
        # Buscar turno (deve existir)
        try:
            turno = Turno.objects.get(nome=data['turno_nome'])
            data['turno'] = turno
        except Turno.DoesNotExist:
            raise serializers.ValidationError({
                'turno_nome': f'Turno "{data["turno_nome"]}" não encontrado.'
            })
        
        return data
    
    def create(self, validated_data):
        """Cria ou atualiza um funcionário."""
        # Remove campos auxiliares
        validated_data.pop('departamento_nome', None)
        validated_data.pop('cargo_nome', None)
        validated_data.pop('turno_nome', None)
        
        # Atualiza ou cria o funcionário
        funcionario, created = Funcionario.objects.update_or_create(
            matricula=validated_data['matricula'],
            defaults=validated_data
        )
        return funcionario
