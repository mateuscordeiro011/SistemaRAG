# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copia apenas os arquivos de dependência primeiro (cache do Docker)
COPY package*.json ./

# Instala as dependências
RUN npm install

# Copia o restante do código
COPY . .

# Expõe a porta padrão do React (3000)
EXPOSE 3000

# Comando de desenvolvimento (hot-reload habilitado pelo volume no docker-compose)
CMD ["npm", "start"]