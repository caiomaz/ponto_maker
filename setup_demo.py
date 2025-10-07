#!/usr/bin/env python
"""
Script de setup para demonstração do Sistema de Ponto Eletrônico Maker.

Este script cria dados de exemplo para facilitar testes e demonstrações.
Execute com: python manage.py shell < setup_demo.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.authtoken.models import Token
from core.models import Departamento, Cargo, Turno, Funcionario, RegistroPonto
from datetime import time, datetime, timedelta
from django.utils import timezone

print("=" * 60)
print("SETUP DE DEMONSTRAÇÃO - SISTEMA DE PONTO ELETRÔNICO MAKER")
print("=" * 60)

# 1. Criar superusuário (se não existir)
print("\n1. Criando superusuário...")
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@empresa.com',
        password='admin123'
    )
    print(f"   ✓ Superusuário criado: admin / admin123")
else:
    admin = User.objects.get(username='admin')
    print(f"   ✓ Superusuário já existe: admin")

# 2. Criar usuário para terminal
print("\n2. Criando usuário para terminal biométrico...")
if not User.objects.filter(username='terminal01').exists():
    terminal_user = User.objects.create_user(
        username='terminal01',
        password='terminal123'
    )
    token = Token.objects.create(user=terminal_user)
    print(f"   ✓ Usuário terminal criado: terminal01")
    print(f"   ✓ Token: {token.key}")
else:
    terminal_user = User.objects.get(username='terminal01')
    token, created = Token.objects.get_or_create(user=terminal_user)
    print(f"   ✓ Usuário terminal já existe: terminal01")
    print(f"   ✓ Token: {token.key}")

# 3. Criar grupos e permissões
print("\n3. Criando grupos de permissões...")

# Grupo RH
if not Group.objects.filter(name='RH').exists():
    grupo_rh = Group.objects.create(name='RH')
    content_type = ContentType.objects.get_for_model(RegistroPonto)
    perms = Permission.objects.filter(content_type=content_type)
    grupo_rh.permissions.set(perms)
    print(f"   ✓ Grupo 'RH' criado com todas as permissões")
else:
    print(f"   ✓ Grupo 'RH' já existe")

# Grupo Gestores
if not Group.objects.filter(name='Gestores').exists():
    grupo_gestores = Group.objects.create(name='Gestores')
    content_type = ContentType.objects.get_for_model(RegistroPonto)
    perm_view = Permission.objects.get(
        content_type=content_type,
        codename='can_view_all_reports'
    )
    grupo_gestores.permissions.add(perm_view)
    print(f"   ✓ Grupo 'Gestores' criado com permissão de visualização")
else:
    print(f"   ✓ Grupo 'Gestores' já existe")

# 4. Criar estrutura organizacional
print("\n4. Criando estrutura organizacional...")

departamentos = ['TI', 'RH', 'Financeiro', 'Comercial']
for nome in departamentos:
    dept, created = Departamento.objects.get_or_create(nome=nome)
    if created:
        print(f"   ✓ Departamento criado: {nome}")

cargos = ['Desenvolvedor', 'Analista', 'Gerente', 'Assistente', 'Coordenador']
for nome in cargos:
    cargo, created = Cargo.objects.get_or_create(nome=nome)
    if created:
        print(f"   ✓ Cargo criado: {nome}")

turnos_data = [
    ('Comercial', time(9, 0), time(18, 0), 60, 5),
    ('Noturno', time(22, 0), time(6, 0), 30, 10),
    ('Manhã', time(6, 0), time(14, 0), 30, 5),
]

for nome, inicio, fim, intervalo, tolerancia in turnos_data:
    turno, created = Turno.objects.get_or_create(
        nome=nome,
        defaults={
            'hora_inicio': inicio,
            'hora_fim': fim,
            'duracao_intervalo_minutos': intervalo,
            'tolerancia_atraso_minutos': tolerancia
        }
    )
    if created:
        print(f"   ✓ Turno criado: {nome}")

# 5. Criar funcionários de exemplo
print("\n5. Criando funcionários de exemplo...")

dept_ti = Departamento.objects.get(nome='TI')
dept_rh = Departamento.objects.get(nome='RH')
cargo_dev = Cargo.objects.get(nome='Desenvolvedor')
cargo_analista = Cargo.objects.get(nome='Analista')
turno_comercial = Turno.objects.get(nome='Comercial')

funcionarios_data = [
    ('João Silva', '10001', 'joao.silva@empresa.com', 1001, dept_ti, cargo_dev),
    ('Maria Santos', '10002', 'maria.santos@empresa.com', 1002, dept_rh, cargo_analista),
    ('Pedro Oliveira', '10003', 'pedro.oliveira@empresa.com', 1003, dept_ti, cargo_dev),
]

for nome, matricula, email, bio_id, dept, cargo in funcionarios_data:
    func, created = Funcionario.objects.get_or_create(
        matricula=matricula,
        defaults={
            'nome_completo': nome,
            'email': email,
            'biometric_id': bio_id,
            'status': 'Ativo',
            'departamento': dept,
            'cargo': cargo,
            'turno': turno_comercial
        }
    )
    if created:
        print(f"   ✓ Funcionário criado: {nome} ({matricula})")

# 6. Criar registros de ponto de exemplo
print("\n6. Criando registros de ponto de exemplo...")

funcionario = Funcionario.objects.get(matricula='10001')
hoje = timezone.now().date()

registros = [
    (funcionario, timezone.make_aware(datetime.combine(hoje, time(9, 0))), 'Entrada'),
    (funcionario, timezone.make_aware(datetime.combine(hoje, time(12, 0))), 'Início Intervalo'),
    (funcionario, timezone.make_aware(datetime.combine(hoje, time(13, 0))), 'Fim Intervalo'),
    (funcionario, timezone.make_aware(datetime.combine(hoje, time(18, 0))), 'Saída'),
]

for func, timestamp, tipo in registros:
    reg, created = RegistroPonto.objects.get_or_create(
        funcionario=func,
        timestamp=timestamp,
        tipo=tipo,
        defaults={'origem': 'Terminal Biométrico'}
    )
    if created:
        print(f"   ✓ Registro criado: {func.nome_completo} - {tipo} - {timestamp.strftime('%H:%M')}")

print("\n" + "=" * 60)
print("SETUP CONCLUÍDO COM SUCESSO!")
print("=" * 60)
print("\nCredenciais de acesso:")
print("  Admin: admin / admin123")
print("  Terminal: terminal01 / terminal123")
print(f"  Token Terminal: {token.key}")
print("\nAcesse o admin em: http://localhost:8000/admin")
print("Acesse a API em: http://localhost:8000/api/v1/")
print("=" * 60)
