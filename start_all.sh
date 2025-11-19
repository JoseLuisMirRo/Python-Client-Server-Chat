#!/bin/bash
# Script para iniciar todos los servicios del Chat Seguro
# Uso: ./start_all.sh

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}🚀 INICIANDO CHAT SEGURO${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    exit 1
fi

# Verificar si las dependencias están instaladas
echo -e "${YELLOW}📦 Verificando dependencias...${NC}"
if ! python3 -c "import websockets" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Instalando dependencias...${NC}"
    pip install -r requirements.txt
fi

# Verificar si existen los certificados SSL
if [ ! -f "server_cert.pem" ] || [ ! -f "server_key.pem" ]; then
    echo -e "${YELLOW}🔐 Generando certificados SSL...${NC}"
    python3 scripts/generate_ssl_certificates.py
fi

# Crear directorio para archivos estáticos si no existe
mkdir -p auth/static/css
mkdir -p auth/static/js

echo -e "\n${GREEN}✅ Verificaciones completadas${NC}\n"

# Función para manejar Ctrl+C
cleanup() {
    echo -e "\n\n${YELLOW}🛑 Deteniendo todos los servicios...${NC}"
    kill $(jobs -p) 2>/dev/null
    wait
    echo -e "${GREEN}👋 ¡Hasta luego!${NC}\n"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}📋 INICIANDO SERVICIOS${NC}"
echo -e "${BLUE}=================================${NC}\n"

# 1. Iniciar servidor TCP de chat
echo -e "${GREEN}1️⃣  Iniciando servidor TCP de chat (puerto 5555)...${NC}"
python3 server/server.py &
CHAT_PID=$!
sleep 2

# 2. Iniciar servidor WebSocket (puente)
echo -e "${GREEN}2️⃣  Iniciando servidor WebSocket (puerto 5001)...${NC}"
python3 websocket_server.py &
WS_PID=$!
sleep 2

# 3. Iniciar servidor web Flask (OAuth + Frontend)
echo -e "${GREEN}3️⃣  Iniciando servidor web Flask (puerto 5000)...${NC}"
python3 web_server.py &
WEB_PID=$!

echo -e "\n${BLUE}=================================${NC}"
echo -e "${GREEN}✅ TODOS LOS SERVICIOS INICIADOS${NC}"
echo -e "${BLUE}=================================${NC}\n"

echo -e "${YELLOW}📍 URLs de acceso:${NC}"
echo -e "   🌐 Web Interface:     ${BLUE}http://localhost:5000${NC}"
echo -e "   🔌 WebSocket:         ${BLUE}ws://localhost:5001${NC}"
echo -e "   🖥️  Chat Server:       ${BLUE}localhost:5555${NC}"

echo -e "\n${YELLOW}📋 Instrucciones:${NC}"
echo -e "   1. Abre tu navegador en: ${BLUE}http://localhost:5000${NC}"
echo -e "   2. Inicia sesión con Google OAuth"
echo -e "   3. Ingresa la contraseña del servidor: ${GREEN}secreto${NC}"
echo -e "   4. ¡Comienza a chatear! 💬"

echo -e "\n${YELLOW}⚠️  Presiona Ctrl+C para detener todos los servicios${NC}\n"

# Esperar a que terminen los procesos (o Ctrl+C)
wait