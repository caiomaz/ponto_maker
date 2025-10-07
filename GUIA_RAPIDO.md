# Guia Rápido - Sistema de Ponto Eletrônico Maker

## 🚀 Início Rápido

### 1. Instalação

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Criar dados de demonstração
python setup_demo.py

# Iniciar servidor
python manage.py runserver
```

### 2. Acessos

- **Admin**: http://localhost:8000/admin
  - Usuário: `admin`
  - Senha: `admin123`

- **API**: http://localhost:8000/api/v1/

- **Token Terminal**: `a19de1f5c9da8b49e99da3d8b7d5490ba8429f9a`

## 📡 Testando a API

### Obter Token JWT

```bash
curl -X POST http://localhost:8000/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Listar Funcionários

```bash
curl -X GET http://localhost:8000/api/v1/funcionarios/ \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

### Registrar Ponto (Terminal)

```bash
curl -X POST http://localhost:8000/api/v1/ponto/registrar/ \
  -H "Authorization: Token a19de1f5c9da8b49e99da3d8b7d5490ba8429f9a" \
  -H "Content-Type: application/json" \
  -d '{"biometric_id": 1001, "tipo": "Entrada"}'
```

### Sincronizar IDs Biométricos

```bash
curl -X GET http://localhost:8000/api/v1/funcionarios/sincronizar/ \
  -H "Authorization: Token a19de1f5c9da8b49e99da3d8b7d5490ba8429f9a"
```

### Gerar Relatório de Folha de Ponto

```bash
curl -X GET "http://localhost:8000/api/v1/relatorios/folha-ponto/?matricula_funcionario=10001&data_inicio=2024-10-01&data_fim=2024-10-31" \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

## 🔐 Configurando Permissões

1. Acesse o Django Admin
2. Vá em **Grupos** (Groups)
3. Crie um novo grupo (ex: "Operadores")
4. Selecione as permissões desejadas:
   - `can_adjust_ponto`: Ajustar ponto manualmente
   - `can_view_all_reports`: Ver todos os relatórios
   - `can_export_data`: Exportar dados
5. Adicione usuários ao grupo

## 📊 Estrutura de Dados

### Funcionário de Exemplo

```json
{
  "nome_completo": "João Silva",
  "matricula": "10001",
  "email": "joao.silva@empresa.com",
  "biometric_id": 1001,
  "status": "Ativo",
  "departamento": 1,
  "cargo": 1,
  "turno": 1
}
```

### Registro de Ponto

```json
{
  "biometric_id": 1001,
  "tipo": "Entrada"
}
```

**Tipos válidos**: `Entrada`, `Saída`, `Início Intervalo`, `Fim Intervalo`

## 📥 Importação de Funcionários

### Formato CSV

```csv
nome_completo,matricula,email,biometric_id,status,departamento_nome,cargo_nome,turno_nome
João Silva,12345,joao@empresa.com,1001,Ativo,TI,Desenvolvedor,Comercial
```

### Importar via API

```bash
curl -X POST http://localhost:8000/api/v1/funcionarios/import_csv/ \
  -H "Authorization: Bearer SEU_TOKEN_JWT" \
  -F "file=@exemplo_importacao.csv"
```

## 📤 Exportação de Dados

### Exportar Funcionários (CSV)

```bash
curl -X GET http://localhost:8000/api/v1/funcionarios/export_csv/ \
  -H "Authorization: Bearer SEU_TOKEN_JWT" \
  -o funcionarios.csv
```

### Exportar Funcionários (Excel)

```bash
curl -X GET http://localhost:8000/api/v1/funcionarios/export_excel/ \
  -H "Authorization: Bearer SEU_TOKEN_JWT" \
  -o funcionarios.xlsx
```

## 🧪 Executar Testes

```bash
python manage.py test
```

## 📝 Dados de Demonstração

O script `setup_demo.py` cria:

- **Departamentos**: TI, RH, Financeiro, Comercial
- **Cargos**: Desenvolvedor, Analista, Gerente, Assistente, Coordenador
- **Turnos**: Comercial (9h-18h), Noturno (22h-6h), Manhã (6h-14h)
- **Funcionários**: 3 funcionários de exemplo
- **Grupos**: RH (todas permissões), Gestores (visualização)
- **Registros**: Registros de ponto do dia atual para João Silva

## 🔧 Troubleshooting

### Erro de autenticação

Verifique se o token está correto e no formato adequado:
- Token: `Authorization: Token <token>`
- JWT: `Authorization: Bearer <token>`

### Permissão negada

Verifique se o usuário possui as permissões necessárias no Django Admin.

### Funcionário não encontrado

Certifique-se de que o `biometric_id` está cadastrado e o funcionário está com status "Ativo".

## 📚 Documentação Completa

Consulte o arquivo `README.md` para documentação completa da API e arquitetura do sistema.
