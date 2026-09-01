#!/bin/bash

# ============================================
# MANAGE SCRIPT - RAG SYSTEM
# ============================================
# Gerencia operações comuns do projeto

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_help() {
    echo -e "${BLUE}RAG System Management${NC}"
    echo ""
    echo "Uso: ./manage.sh <comando>"
    echo ""
    echo "Comandos:"
    echo "  ${GREEN}start${NC}           - Inicia containers"
    echo "  ${GREEN}stop${NC}            - Para containers"
    echo "  ${GREEN}restart${NC}         - Reinicia containers"
    echo "  ${GREEN}logs${NC}            - Mostra logs (adicione 'backend', 'frontend', 'db')"
    echo "  ${GREEN}status${NC}          - Mostra status dos containers"
    echo "  ${GREEN}clean${NC}           - Remove containers e volumes"
    echo "  ${GREEN}test${NC}            - Executa testes da API"
    echo "  ${GREEN}shell-backend${NC}   - Abre shell no container backend"
    echo "  ${GREEN}shell-frontend${NC}  - Abre shell no container frontend"
    echo "  ${GREEN}db-shell${NC}        - Abre shell do MySQL"
    echo "  ${GREEN}db-backup${NC}       - Faz backup do banco de dados"
    echo "  ${GREEN}db-restore${NC}      - Restaura backup do banco"
    echo "  ${GREEN}health${NC}          - Verifica saúde dos serviços"
    echo "  ${GREEN}reset${NC}           - Reset completo (CUIDADO: apaga dados!)"
    echo ""
}

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
# COMANDOS
# ============================================

start() {
    print_info "Iniciando containers..."
    docker-compose up -d
    print_success "Containers iniciados"
    
    print_info "Aguardando serviços..."
    sleep 3
    
    health
}

stop() {
    print_info "Parando containers..."
    docker-compose down
    print_success "Containers parados"
}

restart() {
    stop
    start
}

logs() {
    if [ -z "$1" ]; then
        print_info "Mostrando logs de todos os containers..."
        docker-compose logs -f
    elif [ "$1" == "backend" ]; then
        docker-compose logs -f backend
    elif [ "$1" == "frontend" ]; then
        docker-compose logs -f frontend
    elif [ "$1" == "db" ]; then
        docker-compose logs -f db
    else
        print_error "Serviço desconhecido: $1"
        print_info "Opções: backend, frontend, db"
    fi
}

status() {
    print_info "Status dos containers:"
    docker-compose ps
}

health() {
    echo ""
    print_info "Verificando saúde dos serviços..."
    echo ""
    
    # Backend
    if curl -s http://localhost:8000/health &> /dev/null; then
        print_success "Backend: OK"
    else
        print_error "Backend: ERRO"
    fi
    
    # Frontend
    if curl -s http://localhost:3000 &> /dev/null; then
        print_success "Frontend: OK"
    else
        print_error "Frontend: ERRO"
    fi
    
    # MySQL
    if docker-compose exec -T db mysqladmin ping -h localhost &> /dev/null; then
        print_success "MySQL: OK"
    else
        print_error "MySQL: ERRO"
    fi
    
    echo ""
}

clean() {
    print_error "Removendo containers e volumes..."
    read -p "Tem certeza? Isso irá deletar todos os dados. (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        docker-compose down -v
        print_success "Limpeza concluída"
    else
        print_info "Cancelado"
    fi
}

test_api() {
    print_info "Testando API endpoints..."
    echo ""
    
    BASE_URL="http://localhost:8000"
    
    # Health
    print_info "GET /health"
    curl -s "$BASE_URL/health" | python3 -m json.tool
    echo ""
    
    # Status
    print_info "GET /status"
    curl -s "$BASE_URL/status" | python3 -m json.tool
    echo ""
    
    # Listar clientes
    print_info "GET /clientes"
    curl -s "$BASE_URL/clientes" | python3 -m json.tool
    echo ""
    
    print_success "Testes concluídos"
}

shell_backend() {
    print_info "Abrindo shell no backend..."
    docker-compose exec backend /bin/bash
}

shell_frontend() {
    print_info "Abrindo shell no frontend..."
    docker-compose exec frontend /bin/sh
}

db_shell() {
    print_info "Abrindo shell do MySQL..."
    docker-compose exec db mysql -u root -p
}

db_backup() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="backups/rag_system_backup_$TIMESTAMP.sql"
    
    mkdir -p backups
    
    print_info "Fazendo backup do banco de dados..."
    docker-compose exec -T db mysqldump -u root -p"${DB_ROOT_PASSWORD:-root_password}" \
        rag_system_db > "$BACKUP_FILE"
    
    if [ -f "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        print_success "Backup criado: $BACKUP_FILE ($SIZE)"
    else
        print_error "Erro ao criar backup"
    fi
}

db_restore() {
    if [ -z "$1" ]; then
        print_error "Especifique o arquivo de backup"
        echo "Backup disponíveis:"
        ls -lh backups/
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Arquivo não encontrado: $1"
        exit 1
    fi
    
    read -p "Restaurar backup? Dados atuais serão sobrescrito! (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        print_info "Restaurando backup..."
        docker-compose exec -T db mysql -u root -p"${DB_ROOT_PASSWORD:-root_password}" \
            rag_system_db < "$1"
        print_success "Backup restaurado"
    else
        print_info "Cancelado"
    fi
}

reset() {
    print_error "⚠️  RESET COMPLETO - TODOS OS DADOS SERÃO DELETADOS!"
    read -p "Digite 'SIM' em maiúsculas para confirmar: " confirmation
    
    if [ "$confirmation" != "SIM" ]; then
        print_info "Cancelado"
        exit 0
    fi
    
    print_error "Resetando sistema..."
    
    # Parar containers
    docker-compose down -v
    
    # Limpar arquivos
    rm -rf backend/uploads/*
    rm -rf backend/logs/*
    rm -rf frontend/node_modules
    rm -rf frontend/build
    
    # Reconstruir
    docker-compose build
    docker-compose up -d
    
    print_success "Sistema resetado"
    health
}

# ============================================
# MAIN
# ============================================

if [ -z "$1" ]; then
    print_help
    exit 0
fi

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs "$2"
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    test)
        test_api
        ;;
    shell-backend)
        shell_backend
        ;;
    shell-frontend)
        shell_frontend
        ;;
    db-shell)
        db_shell
        ;;
    db-backup)
        db_backup
        ;;
    db-restore)
        db_restore "$2"
        ;;
    health)
        health
        ;;
    reset)
        reset
        ;;
    *)
        print_error "Comando desconhecido: $1"
        print_help
        exit 1
        ;;
esac
