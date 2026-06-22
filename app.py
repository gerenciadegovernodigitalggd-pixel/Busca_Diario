import json
import os
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, request, send_file


BASE_URL = "https://www.diariomunicipal.com.br/amm-mg"
SEARCH_URL = f"{BASE_URL}/pesquisar"
ENTIDADE = "760"
ORGAO = "1379"

app = Flask(__name__)


def criar_sessao():
    sessao = requests.Session()
    sessao.trust_env = False
    sessao.headers.update({"User-Agent": "Mozilla/5.0"})
    return sessao


def enviar_evento(tipo, dados):
    payload = json.dumps({"type": tipo, **dados}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def obter_token(sessao):
    resp = sessao.get(SEARCH_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    campo = soup.find("input", {"name": "busca_avancada[_token]"})
    if not campo or not campo.get("value"):
        raise RuntimeError("Token da pagina nao encontrado.")
    return campo["value"]


def buscar_stream(palavras, data_inicio, data_fim):
    sessao = criar_sessao()
    token = obter_token(sessao)
    vistos = set()
    total = 0

    for palavra in palavras:
        pagina = 1

        while True:
            yield enviar_evento("status", {
                "message": f"Buscando '{palavra}' - pagina {pagina}",
                "page": pagina,
                "total": total,
            })

            params = {
                "busca_avancada[page]": pagina,
                "busca_avancada[entidadeUsuaria]": ENTIDADE,
                "busca_avancada[nome_orgao]": ORGAO,
                "busca_avancada[texto]": palavra,
                "busca_avancada[dataInicio]": data_inicio,
                "busca_avancada[dataFim]": data_fim,
                "busca_avancada[_token]": token,
            }

            resp = sessao.get(SEARCH_URL, params=params, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            linhas = soup.select("#datatable tbody tr")

            if not linhas:
                break

            for linha in linhas:
                links = linha.find_all("a")
                if len(links) < 2:
                    continue

                href = links[0].get("href", "")
                if "/amm-mg/load/" not in href:
                    continue

                codigo = href.split("/")[-1]
                titulo = links[1].text.strip()
                link = f"{BASE_URL}/load/{codigo}"

                if link in vistos:
                    continue

                vistos.add(link)
                total += 1
                yield enviar_evento("result", {
                    "title": titulo,
                    "link": link,
                    "total": total,
                    "page": pagina,
                })

            proxima = soup.select_one("#datatable_next")
            href_proxima = proxima.get("href", "") if proxima else ""
            classes_proxima = proxima.get("class", []) if proxima else []

            if not href_proxima or href_proxima == "javascript:void(0)" or "disabled" in classes_proxima:
                break

            pagina += 1

    yield enviar_evento("done", {
        "message": f"Concluido. {total} resultados encontrados.",
        "total": total,
    })


@app.get("/")
def index():
    return send_file("index.html")


@app.get("/api/buscar")
def api_buscar():
    termos = request.args.get("termos", "")
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")
    palavras = [p.strip() for p in termos.split(",") if p.strip()]

    def gerar():
        try:
            if not palavras or not data_inicio or not data_fim:
                yield enviar_evento("error", {"message": "Preencha palavra-chave, data inicio e data fim."})
                return

            yield from buscar_stream(palavras, data_inicio, data_fim)
        except Exception as erro:
            yield enviar_evento("error", {"message": str(erro)})

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return Response(gerar(), mimetype="text/event-stream", headers=headers)


@app.get("/api/url")
def api_url_exemplo():
    params = urlencode({
        "termos": "lei",
        "data_inicio": "01/01/2026",
        "data_fim": "07/01/2026",
    })
    return {"url": f"/api/buscar?{params}"}


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=porta, debug=True, threaded=True)
