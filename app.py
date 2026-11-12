"""Encurtador de links simples — só biblioteca padrão do Python (sem dependências).

Uso:
    python app.py            # sobe em http://localhost:8000
    PORT=5000 python app.py  # porta customizada
"""
import html
import os
import secrets
import sqlite3
import string
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB = os.environ.get("DB_PATH", "links.db")
PORT = int(os.environ.get("PORT", 8000))
ALFABETO = string.ascii_letters + string.digits


def db():
    con = sqlite3.connect(DB)
    con.execute(
        "CREATE TABLE IF NOT EXISTS links ("
        "codigo TEXT PRIMARY KEY, url TEXT NOT NULL, "
        "cliques INTEGER NOT NULL DEFAULT 0, "
        "criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    return con


def url_valida(url):
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc)


def novo_codigo(con, tamanho=6):
    while True:
        codigo = "".join(secrets.choice(ALFABETO) for _ in range(tamanho))
        if not con.execute("SELECT 1 FROM links WHERE codigo=?", (codigo,)).fetchone():
            return codigo


def encurtar(url, codigo=None):
    """Retorna (codigo, erro)."""
    url = url.strip()
    if not url_valida(url):
        return None, "URL inválida (use http:// ou https://)."
    with db() as con:
        if codigo:
            if not all(c in ALFABETO + "-_" for c in codigo) or len(codigo) > 32:
                return None, "Código só pode ter letras, números, - e _ (máx. 32)."
            if con.execute("SELECT 1 FROM links WHERE codigo=?", (codigo,)).fetchone():
                return None, "Esse código já está em uso."
        else:
            existente = con.execute("SELECT codigo FROM links WHERE url=?", (url,)).fetchone()
            if existente:
                return existente[0], None
            codigo = novo_codigo(con)
        con.execute("INSERT INTO links (codigo, url) VALUES (?, ?)", (codigo, url))
    return codigo, None


PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Encurtador</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:640px;margin:3rem auto;padding:0 1rem;color:#222}}
input,button{{font:inherit;padding:.6rem;border-radius:6px;border:1px solid #bbb}}
input[name=url]{{width:100%;box-sizing:border-box;margin-bottom:.5rem}}
input[name=codigo]{{width:50%}}
button{{background:#2da44e;color:#fff;border:0;cursor:pointer}}
.msg{{background:#eef;padding:.7rem;border-radius:6px;margin:1rem 0}}
.erro{{background:#fee}}
table{{width:100%;border-collapse:collapse;margin-top:1.5rem}}
td,th{{text-align:left;padding:.4rem;border-bottom:1px solid #eee;font-size:.9rem}}
td.url{{max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
</style></head><body>
<h1>🔗 Encurtador</h1>
<form method="post" action="/encurtar">
<input name="url" placeholder="https://exemplo.com/link-muito-grande" required>
<input name="codigo" placeholder="código personalizado (opcional)">
<button>Encurtar</button>
</form>
{msg}
<table><tr><th>Link</th><th>Destino</th><th>Cliques</th></tr>{linhas}</table>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _html(self, corpo, status=200):
        dados = corpo.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _home(self, msg="", erro=False):
        with db() as con:
            rows = con.execute(
                "SELECT codigo, url, cliques FROM links ORDER BY criado_em DESC LIMIT 20"
            ).fetchall()
        linhas = "".join(
            f'<tr><td><a href="/{html.escape(c)}">/{html.escape(c)}</a></td>'
            f'<td class="url" title="{html.escape(u)}">{html.escape(u)}</td><td>{n}</td></tr>'
            for c, u, n in rows
        )
        caixa = f'<div class="msg{" erro" if erro else ""}">{msg}</div>' if msg else ""
        self._html(PAGINA.format(msg=caixa, linhas=linhas))

    def do_GET(self):
        caminho = urlparse(self.path).path.strip("/")
        if not caminho:
            return self._home()
        with db() as con:
            row = con.execute("SELECT url FROM links WHERE codigo=?", (caminho,)).fetchone()
            if not row:
                return self._html("<h1>404 — link não encontrado</h1>", 404)
            con.execute("UPDATE links SET cliques = cliques + 1 WHERE codigo=?", (caminho,))
        self.send_response(302)
        self.send_header("Location", row[0])
        self.end_headers()

    def do_POST(self):
        if urlparse(self.path).path != "/encurtar":
            return self._html("<h1>404</h1>", 404)
        tam = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(tam).decode())
        url = form.get("url", [""])[0]
        personalizado = form.get("codigo", [""])[0].strip() or None
        codigo, erro = encurtar(url, personalizado)
        if erro:
            return self._home(html.escape(erro), erro=True)
        host = self.headers.get("Host", f"localhost:{PORT}")
        curto = f"http://{host}/{codigo}"
        self._home(f'Pronto: <a href="{html.escape(curto)}">{html.escape(curto)}</a>')


if __name__ == "__main__":
    print(f"Rodando em http://localhost:{PORT}")
    HTTPServer(("", PORT), Handler).serve_forever()
