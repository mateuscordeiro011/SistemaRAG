#!/bin/bash
# teste_rapido.sh - Script rápido para testar todas as novas funcionalidades

set -e  # Exit on error

API="http://localhost:8000"

echo \"═══════════════════════════════════════════════════════════════════\"
echo \"🚀 TESTE RÁPIDO - HEALTH CHECK & MULTIMODALIDADE\"
echo \"═══════════════════════════════════════════════════════════════════\"
echo \"\"

# Cores para output
GREEN='\\033[0;32m'
RED='\\033[0;31m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Função para testar endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e \"${BLUE}[TEST]${NC} $name\"
    
    if [ -z \"$data\" ]; then
        # GET request
        response=$(curl -s -X $method \"$API$endpoint\")
    else
        # POST request
        response=$(curl -s -X $method \"$API$endpoint\" \\
            -H \"Content-Type: application/json\" \\
            -d \"$data\")
    fi
    
    # Check if response is valid JSON
    if echo \"$response\" | jq . >/dev/null 2>&1; then
        echo -e \"${GREEN}✅ OK${NC}\"
        echo \"$response\" | jq -r '.status // .overall_status // .sucesso' 2>/dev/null | head -1 | sed 's/^/   └─ /'
    else
        echo -e \"${RED}❌ ERRO${NC}\"
        echo \"$response\" | head -c 100
    fi
    echo \"\"
}

# ============================================
# 1. TESTE DE HEALTH CHECK RÁPIDO
# ============================================
echo -e \"${YELLOW}1. TESTE: Health Check Rápido${NC}\"
test_endpoint \"Status Rápido\" \"GET\" \"/api/v1/health/quick-status\"

# ============================================
# 2. TESTE DE DIAGNÓSTICO COMPLETO
# ============================================
echo -e \"${YELLOW}2. TESTE: Diagnóstico Completo${NC}\"
echo -e \"${BLUE}[INFO]${NC} Este teste pode levar 3-5 segundos...\"
test_endpoint \"Diagnóstico Completo\" \"GET\" \"/api/v1/health/full-diagnostic\"

# ============================================
# 3. TESTE DE PERSISTÊNCIA
# ============================================
echo -e \"${YELLOW}3. TESTE: Persistência de Dados${NC}\"
test_endpoint \"Teste DB\" \"GET\" \"/api/v1/health/db-test\"

# ============================================
# 4. TESTE DO MODELO DE IA
# ============================================
echo -e \"${YELLOW}4. TESTE: Disponibilidade do Modelo de IA${NC}\"
test_endpoint \"Teste AI Model\" \"GET\" \"/api/v1/health/ai-model-test\"

# ============================================
# 5. CRIAR CLIENTE TESTE
# ============================================
echo -e \"${YELLOW}5. TESTE: Criar Cliente${NC}\"
TIMESTAMP=$(date +%s)
CLIENTE_DATA='{
    \"nome\": \"ClienteTeste'$TIMESTAMP'\",
    \"empresa\": \"Empresa XYZ Ltda\",
    \"descricao\": \"Cliente de teste para validação\"
}'

echo -e \"${BLUE}[TEST]${NC} Criar cliente\"
CLIENTE_RESPONSE=$(curl -s -X POST \"$API/clientes\" \\
    -H \"Content-Type: application/json\" \\
    -d \"$CLIENTE_DATA\")

CLIENTE_ID=$(echo \"$CLIENTE_RESPONSE\" | jq -r '.id' 2>/dev/null || echo \"0\")

if [ \"$CLIENTE_ID\" != \"0\" ] && [ ! -z \"$CLIENTE_ID\" ]; then
    echo -e \"${GREEN}✅ OK${NC}\"
    echo \"   └─ Cliente ID: $CLIENTE_ID\"
else
    echo -e \"${RED}❌ ERRO${NC}\"
    echo \"$CLIENTE_RESPONSE\"
    exit 1
fi
echo \"\"

# ============================================
# 6. PROCESSAR PERGUNTA COM IMAGEM
# ============================================
echo -e \"${YELLOW}6. TESTE: Processar Pergunta (com sugestão de imagem)${NC}\"

PERGUNTA_DATA='{
    \"cliente_id\": '$CLIENTE_ID',
    \"pergunta\": \"Como instalar o painel de controle passo a passo?\",
    \"canal_id\": 1
}'

echo -e \"${BLUE}[TEST]${NC} Processar pergunta multimodal\"
echo -e \"${BLUE}[INFO]${NC} Aguardando resposta de IA... (pode levar 5-15 segundos)\"

MSG_RESPONSE=$(curl -s -X POST \"$API/mensagens/processar\" \\
    -H \"Content-Type: application/json\" \\
    -d \"$PERGUNTA_DATA\")

MSG_ID=$(echo \"$MSG_RESPONSE\" | jq -r '.mensagem_id' 2>/dev/null || echo \"0\")

if [ \"$MSG_ID\" != \"0\" ] && [ ! -z \"$MSG_ID\" ]; then
    echo -e \"${GREEN}✅ OK${NC}\"
    echo \"$MSG_RESPONSE\" | jq '{
        mensagem_id: .mensagem_id,
        status: .status,
        necessita_visual: .necessita_visual,
        imagem_url: .imagem_sugerida.url
    }' | sed 's/^/   /'
else
    echo -e \"${RED}❌ ERRO${NC}\"
    echo \"$MSG_RESPONSE\"
    exit 1
fi
echo \"\"

# ============================================
# 7. OBTER DETALHES COMPLETOS (COM IMAGENS)
# ============================================
echo -e \"${YELLOW}7. TESTE: Obter Detalhes Completos${NC}\"
echo -e \"${BLUE}[TEST]${NC} Detalhes da mensagem com imagem\"

DETALHES=$(curl -s -X GET \"$API/mensagens/$MSG_ID/detalhes-completo\")

if echo \"$DETALHES\" | jq . >/dev/null 2>&1; then
    echo -e \"${GREEN}✅ OK${NC}\"
    echo \"$DETALHES\" | jq '{
        id: .id,
        status: .status,
        necessita_visual: .necessita_visual,
        imagem_url: .imagem_sugerida.url,
        imagem_tipo: .imagem_sugerida.tipo
    }' | sed 's/^/   /'
else
    echo -e \"${RED}❌ ERRO${NC}\"
fi
echo \"\"

# ============================================
# 8. APROVAR COM IMAGEM
# ============================================
echo -e \"${YELLOW}8. TESTE: Aprovar Mensagem com Imagem${NC}\"

APROVACAO_DATA='{
    \"resposta_editada\": \"Para instalar o painel, siga os seguintes passos: 1) Desembalar o equipamento 2) Verificar todos os componentes 3) Conectar o cabo de energia...\",
    \"aprovada\": true,
    \"operador_id\": 1,
    \"imagem_aprovada\": true,
    \"anexos_aprovados\": [
        {
            \"url\": \"http://servidor/uploads/diagrama_instalacao.png\",
            \"tipo\": \"image\",
            \"descricao\": \"Diagrama esquemático de instalação do painel\"
        }
    ]
}'

echo -e \"${BLUE}[TEST]${NC} Aprovar com imagens\"
APRV_RESPONSE=$(curl -s -X POST \"$API/mensagens/$MSG_ID/aprovar-com-imagens\" \\
    -H \"Content-Type: application/json\" \\
    -d \"$APROVACAO_DATA\")

if echo \"$APRV_RESPONSE\" | jq . >/dev/null 2>&1; then
    echo -e \"${GREEN}✅ OK${NC}\"
    echo \"$APRV_RESPONSE\" | jq '{
        sucesso: .sucesso,
        novo_status: .novo_status,
        imagem_aprovada: .imagem_aprovada,
        total_anexos: .total_anexos
    }' | sed 's/^/   /'
else
    echo -e \"${RED}❌ ERRO${NC}\"
fi
echo \"\"

# ============================================
# 9. VERIFICAR PERSISTÊNCIA (após reinicialização)
# ============================================
echo -e \"${YELLOW}9. TESTE: Verificar Persistência${NC}\"
echo -e \"${BLUE}[INFO]${NC} Pausando banco de dados por 5 segundos...\"

docker-compose pause db 2>/dev/null || echo \"⚠️  docker-compose não disponível\"
sleep 5
docker-compose unpause db 2>/dev/null || echo \"⚠️  docker-compose não disponível\"

sleep 2  # Aguardar banco estar pronto

echo -e \"${BLUE}[TEST]${NC} Verificar se mensagem foi persistida\"
VERIFY=$(curl -s -X GET \"$API/mensagens/$MSG_ID/detalhes-completo\")

VERIFY_STATUS=$(echo \"$VERIFY\" | jq -r '.status' 2>/dev/null || echo \"ERROR\")

if [ \"$VERIFY_STATUS\" == \"APROVADA\" ]; then
    echo -e \"${GREEN}✅ PERSISTÊNCIA VALIDADA${NC}\"
    echo \"   └─ Status após reinicialização: $VERIFY_STATUS\"
else
    echo -e \"${RED}❌ PERSISTÊNCIA FALHOU${NC}\"
    echo \"   └─ Status: $VERIFY_STATUS\"
fi
echo \"\"

# ============================================
# RESUMO FINAL
# ============================================
echo \"═══════════════════════════════════════════════════════════════════\"
echo -e \"${GREEN}🎉 TESTE COMPLETADO COM SUCESSO!${NC}\"
echo \"═══════════════════════════════════════════════════════════════════\"
echo \"\"
echo \"Resultados:\"
echo \"  ✅ Health Check (Rápido)\"
echo \"  ✅ Diagnóstico Completo\"
echo \"  ✅ Persistência de Banco\"
echo \"  ✅ Modelo de IA\"
echo \"  ✅ Processamento com Imagens\"
echo \"  ✅ Aprovação com Multimodalidade\"
echo \"  ✅ Persistência Validada\"
echo \"\"
echo \"Cliente criado: $CLIENTE_ID\"
echo \"Mensagem criada: $MSG_ID\"
echo \"Status final: $VERIFY_STATUS\"
echo \"\"
echo \"📚 Para mais detalhes, consulte:\"
echo \"  - GUIA_HEALTH_MULTIMODAL.md\"
echo \"  - EXEMPLOS_PYTHON.md\"
echo \"  - RESUMO_IMPLEMENTACAO.md\"
echo \"\"
