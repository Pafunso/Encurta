# 🔗 Encurtador de Links

Encurtador de links minimalista em Python, **sem dependências** (só biblioteca padrão + SQLite).

## Recursos
- Gera códigos curtos aleatórios (6 caracteres)
- Código personalizado opcional (`/meu-link`)
- Contador de cliques
- Reaproveita o código se a mesma URL for encurtada de novo
- Interface web simples com os últimos 20 links

## Como usar
```bash
python app.py
# abra http://localhost:8000
```

Variáveis opcionais: `PORT` (padrão 8000) e `DB_PATH` (padrão `links.db`).

## Estrutura
- `app.py` — servidor, banco e interface num arquivo só

## Ideias para próximos commits
- Expiração de links
- Endpoint JSON (`POST /api/encurtar`)
- QR Code por link
- Testes com `unittest`
- Dockerfile
