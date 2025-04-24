FROM python:3.11-slim

# Dependências de sistema
RUN apt-get update && apt-get install -y \
    curl git tcpdump iproute2 iputils-ping net-tools \
    && rm -rf /var/lib/apt/lists/*

# Instala Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cria pasta do projeto
WORKDIR /app
COPY scripts/ ./scripts

# Expondo porta padrão do mitmproxy
EXPOSE 8080 8081 8082

# Comando default (pode ser sobrescrito pelo docker-compose)
CMD ["mitmdump", "-s", "scripts/proxy_with_order_intercept.py"]
