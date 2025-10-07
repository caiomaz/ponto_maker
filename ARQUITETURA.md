# Arquitetura do Sistema de Ponto Eletrônico Maker

## 📐 Visão Geral

O Sistema de Ponto Eletrônico Maker foi desenvolvido seguindo uma **arquitetura API-first**, com total desacoplamento entre backend e clientes. A aplicação segue os princípios **SOLID** e utiliza boas práticas de desenvolvimento Django/DRF.

## 🏛️ Princípios SOLID Aplicados

### Single Responsibility Principle (SRP)

Cada classe tem uma única responsabilidade:

- **Models**: Representam apenas a estrutura de dados
- **Serializers**: Responsáveis apenas por validação e serialização
- **Views**: Orquestram requisições HTTP
- **Services**: Contêm lógica de negócio complexa
- **Permissions**: Gerenciam controle de acesso

### Open/Closed Principle (OCP)

O sistema é aberto para extensão, mas fechado para modificação:

- Permissões customizadas podem ser adicionadas sem modificar código existente
- Novos serializers podem ser criados herdando dos existentes
- Sistema de permissões dinâmico via Django Admin

### Liskov Substitution Principle (LSP)

Abstrações podem ser substituídas por suas implementações:

- Views genéricas do DRF podem ser substituídas
- Serializers específicos substituem serializers genéricos conforme necessário

### Interface Segregation Principle (ISP)

Interfaces específicas para cada caso de uso:

- `FuncionarioSerializer`: Completo para CRUD
- `FuncionarioListSerializer`: Simplificado para listagem
- `RegistroPontoTerminalSerializer`: Específico para terminais
- `AjustePontoSerializer`: Específico para ajustes manuais

### Dependency Inversion Principle (DIP)

Views dependem de abstrações (services), não de implementações concretas:

- `RelatorioFolhaPontoService`: Encapsula lógica de geração de relatórios
- `FuncionarioQueryService`: Encapsula lógica de filtros e permissões

## 🔄 Fluxo de Requisição

```
Cliente → URL Router → View → Permission → Serializer → Model → Database
                         ↓
                      Service (lógica de negócio)
```

## 📦 Estrutura de Camadas

### 1. Camada de Apresentação (Views)

**Responsabilidade**: Orquestrar requisições HTTP e respostas

- `DepartamentoViewSet`
- `CargoViewSet`
- `TurnoViewSet`
- `FuncionarioViewSet`
- `RegistroPontoViewSet`
- `RegistroPontoTerminalView`
- `SincronizarFuncionariosView`
- `AjustePontoView`
- `RelatorioFolhaPontoView`

### 2. Camada de Serialização

**Responsabilidade**: Validação e transformação de dados

- Serializers básicos (CRUD)
- Serializers especializados (importação, terminal)
- Validações de negócio

### 3. Camada de Serviços

**Responsabilidade**: Lógica de negócio complexa

- `RelatorioFolhaPontoService`: Cálculo de horas, atrasos e extras
- `FuncionarioQueryService`: Filtros e Row-Level Security

### 4. Camada de Permissões

**Responsabilidade**: Controle de acesso granular

- `CanAdjustPonto`
- `CanViewAllReports`
- `CanExportData`
- `IsTerminalAuthenticated`

### 5. Camada de Dados (Models)

**Responsabilidade**: Representação e persistência de dados

- `Departamento`
- `Cargo`
- `Turno`
- `Funcionario`
- `RegistroPonto`

## 🔐 Sistema de Autenticação

### Autenticação Dupla

1. **Token Authentication** (DRF Token)
   - Para terminais biométricos
   - Token estático por terminal
   - Validado via `IsTerminalAuthenticated`

2. **JWT Authentication** (Simple JWT)
   - Para integrações externas
   - Tokens com expiração
   - Access token (1h) + Refresh token (7 dias)

### Fluxo de Autenticação

```
Terminal → Token → IsTerminalAuthenticated → API Interna
Sistema Externo → JWT → JWTAuthentication → API Externa
```

## 🛡️ Sistema de Permissões

### Arquitetura de Permissões

O sistema utiliza o modelo nativo do Django com três camadas:

1. **Permissões Nativas**: CRUD automático (add, change, delete, view)
2. **Permissões Customizadas**: Definidas no modelo `RegistroPonto`
3. **Row-Level Security**: Implementado em services e views

### Permissões Customizadas

```python
permissions = [
    ('can_adjust_ponto', 'Pode realizar ajustes manuais no ponto'),
    ('can_view_all_reports', 'Pode visualizar todos os relatórios'),
    ('can_export_data', 'Pode exportar dados e relatórios'),
]
```

### Grupos Dinâmicos

Não existem papéis pré-definidos no código. Todos os grupos são criados dinamicamente via Django Admin, permitindo:

- Criação de grupos customizados
- Atribuição flexível de permissões
- Gestão centralizada de acessos

## 📊 Modelo de Dados

### Relacionamentos

```
Departamento ←──┐
                │
Cargo ←─────────┼─── Funcionario ──→ RegistroPonto ──→ User (ajustado_por)
                │
Turno ←─────────┘
```

### Integridade Referencial

- `PROTECT`: Departamento, Cargo, Turno (não podem ser deletados se houver funcionários)
- `CASCADE`: Funcionario → RegistroPonto (registros são deletados com o funcionário)
- `SET_NULL`: User → RegistroPonto (ajustes mantêm histórico mesmo se usuário for deletado)

## 🔄 Padrões de Design Utilizados

### 1. Repository Pattern (implícito via ORM)

```python
Funcionario.objects.filter(status='Ativo')
```

### 2. Service Layer Pattern

```python
service = RelatorioFolhaPontoService(funcionario, data_inicio, data_fim)
relatorio = service.gerar_relatorio()
```

### 3. Strategy Pattern (Serializers)

```python
def get_serializer_class(self):
    if self.action == 'list':
        return FuncionarioListSerializer
    return FuncionarioSerializer
```

### 4. Decorator Pattern (Permissions)

```python
@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanExportData])
def export_csv(self, request):
    ...
```

## 🚀 APIs Disponíveis

### API Interna (Terminais)

- `POST /api/v1/ponto/registrar/`: Registrar ponto
- `GET /api/v1/funcionarios/sincronizar/`: Sincronizar IDs biométricos

### API Externa (Integrações)

- `GET /api/v1/funcionarios/`: Listar/filtrar funcionários
- `GET /api/v1/registros/`: Listar registros de ponto
- `GET /api/v1/relatorios/folha-ponto/`: Gerar relatório
- `POST /api/v1/ajuste-ponto/`: Ajustar ponto manualmente

### Recursos CRUD Completos

- `/api/v1/departamentos/`
- `/api/v1/cargos/`
- `/api/v1/turnos/`
- `/api/v1/funcionarios/`
- `/api/v1/registros/`

## 📈 Escalabilidade

### Pontos de Extensão

1. **Novos Tipos de Registro**: Adicionar choices em `RegistroPonto.tipo`
2. **Novos Relatórios**: Criar novos services e views
3. **Novas Permissões**: Adicionar em `RegistroPonto.Meta.permissions`
4. **Novos Filtros**: Estender `FuncionarioQueryService`

### Otimizações Possíveis

1. **Cache**: Redis para dados frequentemente acessados
2. **Paginação**: Já implementada via DRF
3. **Select Related**: Otimizar queries com `select_related()` e `prefetch_related()`
4. **Índices**: Adicionar índices em campos frequentemente filtrados

## 🧪 Estratégia de Testes

### Cobertura de Testes

1. **Testes de Modelo**: Validação de criação e relacionamentos
2. **Testes de API**: Endpoints e respostas HTTP
3. **Testes de Permissão**: Controle de acesso
4. **Testes de Serialização**: Validações de dados

### Tipos de Testes

- **Unitários**: Lógica isolada (models, serializers)
- **Integração**: Fluxo completo (API endpoints)
- **Permissões**: Controle de acesso

## 📝 Boas Práticas Implementadas

1. ✅ Separação de responsabilidades (SOLID)
2. ✅ Validação em múltiplas camadas
3. ✅ Documentação inline (docstrings)
4. ✅ Type hints implícitos via Django
5. ✅ Tratamento de erros adequado
6. ✅ Logs de auditoria (ajustado_por)
7. ✅ Versionamento de API (v1)
8. ✅ Paginação automática
9. ✅ Filtros dinâmicos
10. ✅ Exportação de dados

## 🔮 Próximas Evoluções

1. **Notificações**: Sistema de alertas para atrasos
2. **Dashboard**: Interface web para visualização
3. **Relatórios Avançados**: Gráficos e análises
4. **Integração Biométrica**: SDK para dispositivos
5. **Mobile App**: Aplicativo para funcionários
6. **Geolocalização**: Validação de localização no registro
7. **Reconhecimento Facial**: Alternativa à biometria digital
