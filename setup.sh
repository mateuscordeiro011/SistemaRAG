#!/bin/bash

# ============================================
# SETUP SCRIPT - RAG SYSTEM
# ============================================
# Este script configura o ambiente para
# desenvolvimento local ou container

set -e  # Exit on error

echo "============================================"
echo "RAG SYSTEM - SETUP INICIAL"
echo "============================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================
# FUNÇÕES HELPER
# ============================================

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# ============================================
# VERIFICAR PRÉ-REQUISITOS
# ============================================

print_info "Verificando pré-requisitos..."

if ! command -v docker &> /dev/null; then
    print_error "Docker não encontrado. Por favor, instale Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose não encontrado. Por favor, instale Docker Compose"
    exit 1
fi

print_success "Docker e Docker Compose encontrados"

# ============================================
# CRIAR ARQUIVOS .ENV
# ============================================

print_info "Configurando arquivos .env..."

if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    print_success "Criado backend/.env"
    print_info "⚠️ IMPORTANTE: Edite backend/.env e adicione sua OPENAI_API_KEY"
else
    print_info "backend/.env já existe"
fi

if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    print_success "Criado frontend/.env"
else
    print_info "frontend/.env já existe"
fi

# ============================================
# CRIAR DIRETÓRIOS NECESSÁRIOS
# ============================================

print_info "Criando diretórios..."

mkdir -p backend/uploads
mkdir -p backend/logs
print_success "Diretórios criados"

# ============================================
# BUILD E START CONTAINERS
# ============================================

print_info "Construindo e iniciando containers..."

docker-compose build
print_success "Containers construídos"

docker-compose up -d
print_success "Containers iniciados"

# ============================================
# AGUARDAR SERVIÇOS
# ============================================

print_info "Aguardando serviços ficarem prontos..."

# Aguardar MySQL
for i in {1..30}; do
    if docker-compose exec -T db mysqladmin ping -h localhost &> /dev/null; then
        print_success "MySQL está pronto"
        break
    fi
    echo -n "."
    sleep 1
done

# Aguardar Backend
for i in {1..30}; do
    if curl -s http://localhost:8000/health &> /dev/null; then
        print_success "Backend está pronto"
        break
    fi
    echo -n "."
    sleep 1
done

# ============================================
# CRIAR CLIENTE DE TESTE
# ============================================

print_info "Criando cliente de teste..."

curl -s -X POST http://localhost:8000/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Cliente Teste",
    "empresa": "Empresa XYZ",
    "descricao": "Cliente de teste para desenvolvimento"
  }' > /dev/null

print_success "Cliente de teste criado"

# ============================================
# EXIBIR INFORMAÇÕES FINAIS
# ============================================

echo ""
echo "============================================"
echo "SETUP CONCLUÍDO COM SUCESSO!"
echo "============================================"
echo ""
echo "Serviços disponíveis em:"
echo -e "  ${GREEN}Frontend:${NC}  http://localhost:3000"
echo -e "  ${GREEN}Backend:${NC}   http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC}  http://localhost:8000/docs"
echo -e "  ${GREEN}MySQL:${NC}     localhost:3306"
echo ""
echo "Próximas ações:"
echo "  1. Edite backend/.env com sua OPENAI_API_KEY"
echo "  2. Upload um documento em http://localhost:3000"
echo "  3. Teste a pergunta e aprovação"
echo ""
echo "Para visualizar logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f frontend"
echo ""
echo "Para parar os serviços:"
echo "  docker-compose down"
echo ""

# ============================================
# LIMPAR E RESETAR (OPCIONAL)
# ============================================

read -p "Gostaria de criar um documento de teste? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    print_info "Criando documento de teste..."
    
    # Criar arquivo teste
    cat > /tmp/test_document.txt << 'EOF'
POLÍTICA DE ATENDIMENTO

1. HORÁRIO DE FUNCIONAMENTO
   - Segunda a Sexta: 8h às 18h
   - Sábado: 9h às 13h
   - Domingos e feriados: Fechado

2. TEMPO DE RESPOSTA
   - Chat: Até 2 horas durante horário comercial
   - Email: Até 24 horas
   - Telefone: Atendimento imediato

3. POLÍTICA DE REEMBOLSO
   - Prazo: 30 dias corridos após compra
   - Condição: Produto em perfeito estado
   - Processo: Solicitar RMA via email
   - Devolução de valores: 3-5 dias úteis

4. GARANTIA
   - Produtos: 1 ano de garantia
   - Defeito de fabricação: Coberto
   - Danos acidentais: Não coberto
   - Exposição a água: Anula garantia

5. CONTATO
   - Email: suporte@empresa.com
   - Telefone: (11) 3000-0000
   - Chat: Disponível no site
EOF
    
    curl -s -F "file=@/tmp/test_document.txt" \
         "http://localhost:8000/documentos/upload?cliente_id=1" > /dev/null
    
    print_success "Documento de teste criado"
    echo ""
    print_info "Agora você pode fazer uma pergunta como:"
    echo "  'Qual é o prazo para reembolso?'"
    echo ""
fi

print_success "Setup concluído! Bem-vindo ao RAG System 🚀"
