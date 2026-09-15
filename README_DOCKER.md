# 🐳 RAG System - Guia de Execução com Docker Compose

## 📋 Pré-requisitos

- **Docker** (versão 20.10+)
- **Docker Compose** (versão 2.0+)
- **MySQL Workbench** (opcional, para monitoramento do banco)

## 🚀 Como Rodar o Sistema

### 1. Clone e configure o ambiente

```bash
cd /workspace

# Copie o arquivo de exemplo e ajuste as variáveis
cp .env.example .env

# Edite o arquivo .env e adicione sua OpenAI API Key
echo "OPENAI_API_KEY=sk-sua-chave-aqui" >> .env
```

### 2. Inicie todos os serviços

```bash
docker-compose up -d --build
```

### 3. Verifique o status dos containers

```bash
docker-compose ps
```

### 4. Acesse as aplicações

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | http://localhost:3000 | Interface React do sistema |
| **Backend API** | http://localhost:8000 | API FastAPI + Swagger Docs |
| **MySQL** | localhost:3306 | Banco de dados (Workbench) |

### 5. MySQL Workbench Connection

Para conectar o MySQL Workbench ao banco:

- **Hostname:** `localhost`
- **Port:** `3306`
- **Username:** `rag_user`
- **Password:** `rag_password`
- **Database:** `sistema_rag`

## 🔧 Comandos Úteis

### Ver logs em tempo real

```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Apenas MySQL
docker-compose logs -f db
```

### Parar o sistema

```bash
docker-compose down
```

### Parar e remover volumes (limpeza completa)

```bash
docker-compose down -v
```

### Reiniciar um serviço específico

```bash
docker-compose restart backend
```

### Reconstruir um serviço

```bash
docker-compose build --no-cache backend
docker-compose up -d backend
```

## 🏗️ Arquitetura Docker

```
┌─────────────────────────────────────────────────────┐
│                   Docker Network                     │
│                    rag_network                        │
│                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────┐ │
│  │  Frontend   │───▶│   Backend   │───▶│  MySQL   │ │
│  │  (React)    │    │  (FastAPI)  │    │  8.0 DB  │ │
│  │  Port 3000  │    │  Port 8000  │    │  Port    │ │
│  └─────────────┘    └─────────────┘    │  3306    │ │
│         │                  │           └──────────┘ │
│         ▼                  ▼                │        │
│  http://localhost:3000  http://localhost:8000       │
│                         Swagger: /docs              │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
              MySQL Workbench (localhost:3306)
```

## 📁 Estrutura de Arquivos

```
/workspace/
├── docker-compose.yml       # Orquestração dos containers
├── .env                     # Variáveis de ambiente (não commitar)
├── .env.example             # Exemplo de variáveis
├── scripts/
│   └── init.sql             # Script de inicialização do MySQL
├── backend/
│   ├── Dockerfile           # Build da API Python
│   ├── main.py              # Aplicação FastAPI
│   ├── database.py          # Configuração do banco
│   ├── models.py            # Modelos SQLAlchemy
│   ├── rag_engine.py        # Motor RAG (embeddings, busca)
│   ├── ingestion.py         # Processamento de documentos
│   └── requirements.txt     # Dependências Python
└── frontend/
    ├── Dockerfile           # Build do React
    ├── src/
    │   ├── App.jsx          # Componente principal
    │   ├── services/api.js  # Cliente HTTP (Axios)
    │   └── components/      # Componentes React
    └── package.json         # Dependências Node.js
```

## 🔍 Endpoints da API

### Health Check
```bash
curl http://localhost:8000/health
```

### Status do Sistema
```bash
curl http://localhost:8000/status
```

### Upload de Documento
```bash
curl -X POST "http://localhost:8000/documentos/upload?cliente_id=1" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/caminho/do/arquivo.pdf"
```

### Processar Pergunta (RAG)
```bash
curl -X POST "http://localhost:8000/mensagens/processar?cliente_id=1&pergunta=Qual+o+prazo+de+garantia"
```

### Swagger UI
Acesse http://localhost:8000/docs para documentação interativa.

## 🐛 Troubleshooting

### Backend não conecta ao MySQL

Verifique se o MySQL está saudável:
```bash
docker-compose ps db
docker-compose logs db
```

Espere o healthcheck passar antes do backend iniciar.

### Frontend não carrega

Verifique os logs:
```bash
docker-compose logs frontend
```

Confirme que a API_URL está correta no `.env`.

### MySQL Workbench não conecta

1. Verifique se a porta 3306 não está em uso
2. Confirme as credenciais no `.env`
3. Teste via terminal:
```bash
mysql -h 127.0.0.1 -P 3306 -u rag_user -p
```

### Limpeza completa e rebuild

```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

## 📊 Volumes Persistidos

| Volume | Localização | Descrição |
|--------|-------------|-----------|
| `mysql_data` | `/var/lib/mysql` | Dados do MySQL |
| `uploads` | `/app/uploads` | Documentos enviados |

## 🔐 Segurança

⚠️ **IMPORTANTE**: Este setup é para **DESENVOLVIMENTO**. Para produção:

1. Altere todas as senhas padrão
2. Não exponha a porta 3306 publicamente
3. Use HTTPS/TLS para comunicações
4. Implemente autenticação na API
5. Use secrets management para chaves de API

## 📝 Próximos Passos

1. Adicione sua `OPENAI_API_KEY` no `.env`
2. Faça upload de documentos via interface ou API
3. Teste o pipeline RAG fazendo perguntas
4. Monitore o histórico de chats no MySQL Workbench
