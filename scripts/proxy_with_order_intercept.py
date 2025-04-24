from mitmproxy import http, ctx

def request(flow: http.HTTPFlow):
    url = flow.request.pretty_url
    method = flow.request.method

    if method == "POST" and any(x in url for x in ["/order", "/orders", "/trade", "/execute"]):
        order_data = flow.request.get_text()
        ctx.log.info(f"🚀 Ordem interceptada: {url}")
        ctx.log.info(f"📦 Conteúdo da ordem: {order_data[:300].replace(chr(10), ' ')}")
        # Não atrasa a requisição — apenas loga
    else:
        ctx.log.info(f"➡️ Requisição direta: {method} {url}")
