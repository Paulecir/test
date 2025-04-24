from mitmproxy import http, ctx
import asyncio
import time

# Tempo de atraso em segundos
DELAY = 8

# Buffers
ws_buffer = []

# Estado do mercado por cliente
market_state = {}

# Ignorar endpoints irrelevantes
ignore_patterns = [
    "datadoghq", "telemetry", "gtm", "collect", "control.txt", "intake"
]

def should_ignore(url: str):
    return any(p in url for p in ignore_patterns)

# Logger para salvar em arquivo
def log_to_file(message):
    with open("/app/logs/proxy_debug.log", "a", encoding="utf-8") as log_file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {message}\n")

# Função chamada ao iniciar o script
def load(l):
    ctx.log.info("🚀 Proxy com delay iniciado (resposta atrasada HTTP + WS)")
    log_to_file("🚀 Proxy com delay iniciado")
    asyncio.get_event_loop().create_task(delay_replay())

# Filtros de dados de mercado
def is_market_data(url: str):
    url = url.lower()
    return any(x in url for x in ["/prices", "/chart", "/ohlc", "/candles", "/data", "/series", "/snapshot"])

# Atrasar apenas resposta HTTP de dados de mercado
def response(flow: http.HTTPFlow):
    url = flow.request.pretty_url.lower()
    content_type = flow.response.headers.get("content-type", "")

    if should_ignore(url):
        return

    if "application/json" in content_type and is_market_data(url):
        data = flow.response.get_text()
        ctx.log.info(f"🔍 JSON detectado em {url}")
        ctx.log.info(f"📊 Dados (parcial): {data[:300].replace(chr(10), ' ')}")
        log_to_file(f"🔍 JSON detectado em {url}")
        log_to_file(f"📊 Dados (parcial): {data[:300].replace(chr(10), ' ')}")

    if is_market_data(url):
        delay = DELAY
        ctx.log.info(f"⏳ Atrasando resposta HTTP: {url} por {delay}s")
        log_to_file(f"⏳ Atrasando resposta HTTP: {url} por {delay}s")
        asyncio.get_event_loop().call_later(delay, lambda: flow.resume())
        flow.intercept()
    else:
        ctx.log.info(f"🚀 Resposta direta: {url}")
        log_to_file(f"🚀 Resposta direta: {url}")

# Acompanhar mensagens WS e atrasar dados de mercado
def websocket_message(flow):
    if flow.messages:
        msg = flow.messages[-1]
        if msg.from_server:
            content = msg.content.decode("utf-8", errors="ignore")
            if any(x in content.lower() for x in ["ohlc", "candles", "price", "snapshot", "update", "tick", "market"]):
                ctx.log.info(f"📩 WS capturado: {flow.request.host} | {content[:60].replace(chr(10), ' ')}...")
                log_to_file(f"📩 WS capturado: {flow.request.host} | {content[:60].replace(chr(10), ' ')}...")
                msg.drop()
                ws_buffer.append((time.time(), flow, content))
                market_state[flow.client_conn.address] = {
                    "timestamp": time.time(),
                    "data": content
                }

# Liberação dos buffers (delay assíncrono)
async def delay_replay():
    while True:
        now = time.time()

        for t, flow, content in ws_buffer[:]:
            if now - t >= DELAY:
                try:
                    flow.send_message(content)
                    ctx.log.info(f"⏱ WS enviado: {content[:60].replace(chr(10), ' ')}...")
                    log_to_file(f"⏱ WS enviado: {content[:60].replace(chr(10), ' ')}...")
                except Exception as e:
                    ctx.log.warn(f"Erro WS: {e}")
                    log_to_file(f"Erro WS: {e}")
                ws_buffer.remove((t, flow, content))

        await asyncio.sleep(1)
