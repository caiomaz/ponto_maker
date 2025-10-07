# Sistema de Ponto Eletrônico Maker

Sistema completo de gestão de ponto eletrônico desenvolvido com Django e Django REST Framework, seguindo arquitetura API-first e princípios SOLID.

## 📋 Sobre o Projeto

O Sistema de Ponto Eletrônico Maker é uma aplicação web robusta, segura e escalável para gestão de Time and Attendance. O sistema foi projetado com total desacoplamento entre backend e clientes (terminais físicos, sistemas de terceiros), utilizando uma arquitetura API-first.

### Características Principais

- **Arquitetura API-first**: Total desacoplamento entre backend e frontend
- **Autenticação Dupla**: Token para terminais físicos e JWT para integrações externas
- **Sistema de Permissões Dinâmico**: Baseado no sistema nativo do Django (Groups e Permissions)
- **Row-Level Security**: Controle granular de acesso aos dados
- **Importação/Exportação**: Suporte a CSV e Excel
- **Relatórios Automatizados**: Cálculo automático de horas, atrasos e extras

## 🛠️ Stack Tecnológica

- **Python**: 3.10+
- **Framework**: Django 4.2+
- **API**: Django REST Framework
- **Banco de Dados**: SQLite (desenvolvimento)
- **Autenticação**: DRF Token + JWT (Simple JWT)

## 📦 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip
- virtualenv (recomendado)

### Passos de Instalação

1. **Clone o repositório** (ou extraia o arquivo ZIP)

```bash
cd ponto_eletronico
```

2. **Crie e ative o ambiente virtual**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**

```bash
pip install -r requirements.txt
```

4. **Execute as migrações**

```bash
python manage.py migrate
```

5. **Crie um superusuário**

```bash
python manage.py createsuperuser
```

6. **Inicie o servidor de desenvolvimento**

```bash
python manage.py runserver
```

O sistema estará disponível em `http://localhost:8000`

## 🔑 Autenticação

### Para Terminais Biométricos (Token)

1. Acesse o Django Admin em `/admin`
2. Crie um usuário para o terminal
3. Gere um Token em "Auth Token > Tokens"
4. Use o token no header: `Authorization: Token <seu-token>`

### Para Integrações Externas (JWT)

1. Obtenha o token JWT:

```bash
POST /api/v1/token/
{
    "username": "seu_usuario",
    "password": "sua_senha"
}
```

2. Use o token no header: `Authorization: Bearer <seu-token-jwt>`

## 📚 Documentação da API

### API Interna (Terminais)

#### Registrar Ponto

```http
POST /api/v1/ponto/registrar/
Authorization: Token <token>
Content-Type: application/json

{
    "biometric_id": 12345,
    "tipo": "Entrada"
}
```

**Tipos válidos**: `Entrada`, `Saída`, `Início Intervalo`, `Fim Intervalo`

#### Sincronizar Funcionários

```http
GET /api/v1/funcionarios/sincronizar/
Authorization: Token <token>
```

Retorna lista de IDs biométricos ativos.

### API Externa (Integrações)

#### Listar Funcionários

```http
GET /api/v1/funcionarios/?departamento=1&cargo=2&status=Ativo
Authorization: Bearer <jwt-token>
```

#### Listar Registros de Ponto

```http
GET /api/v1/registros/?matricula_funcionario=12345&data_inicio=2024-01-01&data_fim=2024-01-31
Authorization: Bearer <jwt-token>
```

#### Relatório de Folha de Ponto

```http
GET /api/v1/relatorios/folha-ponto/?matricula_funcionario=12345&data_inicio=2024-01-01&data_fim=2024-01-31
Authorization: Bearer <jwt-token>
```

#### Ajuste Manual de Ponto

```http
POST /api/v1/ajuste-ponto/
Authorization: Bearer <jwt-token>
Content-Type: application/json

{
    "funcionario": 1,
    "timestamp": "2024-01-15T09:00:00Z",
    "tipo": "Entrada",
    "justificativa": "Esqueceu de registrar na entrada"
}
```

**Requer permissão**: `can_adjust_ponto`

### Exportação de Dados

Todos os endpoints de listagem possuem ações de exportação:

```http
GET /api/v1/funcionarios/export_csv/
GET /api/v1/funcionarios/export_excel/
GET /api/v1/departamentos/export_csv/
GET /api/v1/cargos/export_csv/
GET /api/v1/turnos/export_csv/
GET /api/v1/registros/export_csv/
```

**Requer permissão**: `can_export_data`

## 🔐 Sistema de Permissões

O sistema utiliza o modelo nativo de permissões do Django, com três permissões customizadas:

1. **can_adjust_ponto**: Permite realizar ajustes manuais no ponto
2. **can_view_all_reports**: Permite visualizar todos os relatórios
3. **can_export_data**: Permite exportar dados e relatórios

### Configurando Permissões

1. Acesse o Django Admin (`/admin`)
2. Vá em "Grupos" (Groups)
3. Crie um novo grupo (ex: "Gestores", "RH", "Operadores")
4. Atribua as permissões desejadas ao grupo
5. Adicione usuários ao grupo

**Importante**: Não existem papéis pré-definidos no código. Todos os níveis de acesso são criados dinamicamente via Django Admin.

## 📊 Modelos de Dados

### Departamento
- `nome`: Nome do departamento (único)

### Cargo
- `nome`: Nome do cargo (único)

### Turno
- `nome`: Nome do turno (único)
- `hora_inicio`: Horário de início
- `hora_fim`: Horário de fim
- `duracao_intervalo_minutos`: Duração do intervalo
- `tolerancia_atraso_minutos`: Tolerância de atraso (padrão: 5 min)

### Funcionario
- `nome_completo`: Nome completo
- `matricula`: Matrícula (único)
- `email`: E-mail corporativo (único)
- `biometric_id`: ID biométrico (único, opcional)
- `status`: Ativo, Inativo, Férias, Demitido
- `departamento`: FK para Departamento
- `cargo`: FK para Cargo
- `turno`: FK para Turno

### RegistroPonto
- `funcionario`: FK para Funcionario
- `timestamp`: Data e hora do registro
- `tipo`: Entrada, Saída, Início Intervalo, Fim Intervalo
- `origem`: Terminal Biométrico, Ajuste Manual
- `justificativa`: Justificativa (obrigatória para ajustes)
- `ajustado_por`: FK para User (quem fez o ajuste)

## 🧪 Testes

Execute os testes com:

```bash
python manage.py test
```

Os testes cobrem:
- Criação de modelos
- Endpoints da API
- Sistema de autenticação
- Sistema de permissões
- Validações de negócio

## 📁 Estrutura do Projeto

```
ponto_eletronico/
├── config/                 # Configurações do projeto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                   # App principal
│   ├── migrations/
│   ├── admin.py           # Configuração do Django Admin
│   ├── models.py          # Modelos de dados
│   ├── serializers.py     # Serializers DRF
│   ├── views.py           # Views da API
│   ├── urls.py            # Rotas da API
│   ├── permissions.py     # Permissões customizadas
│   ├── services.py        # Lógica de negócio
│   └── tests.py           # Testes
├── manage.py
├── requirements.txt
└── README.md
```

## 🏗️ Arquitetura e Princípios

O projeto foi desenvolvido seguindo os princípios SOLID:

- **Single Responsibility**: Cada classe tem uma única responsabilidade
- **Open/Closed**: Extensível sem modificar código existente
- **Liskov Substitution**: Abstrações podem ser substituídas
- **Interface Segregation**: Serializers específicos para cada caso de uso
- **Dependency Inversion**: Views dependem de services (abstrações)

### Camadas da Aplicação

1. **Models**: Representação dos dados (ORM)
2. **Serializers**: Validação e serialização de dados
3. **Services**: Lógica de negócio complexa
4. **Permissions**: Controle de acesso granular
5. **Views**: Orquestração e resposta HTTP
6. **URLs**: Roteamento de requisições

## 🚀 Próximos Passos

Para produção, considere:

1. Migrar para PostgreSQL ou MySQL
2. Configurar variáveis de ambiente (SECRET_KEY, DEBUG, etc)
3. Implementar cache (Redis)
4. Configurar CORS adequadamente
5. Adicionar rate limiting
6. Implementar logging estruturado
7. Configurar backup automático
8. Deploy com Gunicorn + Nginx

## 📄 Licença

Este projeto foi desenvolvido como parte do Sistema de Ponto Eletrônico Maker.

## 👥 Suporte

Para dúvidas ou suporte, consulte a documentação do Django e Django REST Framework:
- [Django Documentation](https://docs.djangoproject.com/)
- [DRF Documentation](https://www.django-rest-framework.org/)
