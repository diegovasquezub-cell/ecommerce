# Agente Ecommerce

Chat de un ecommerce con un **router** (LangGraph + Gemini) que lee el mensaje del cliente y lo enruta a uno de tres agentes:

- `preventa`: productos, precios, tallas, stock, promociones y formas de pago.
- `postventa`: reclamos, seguimiento de pedidos, devoluciones, cambios y garantías.
- `generica`: lo que no tiene que ver con la tienda o saludos sin pedido.

Los agentes destino son cascarones por ahora; lo que está listo es el enrutamiento, una API FastAPI y la memoria por conversación. El endpoint de Telegram es un stub (ver más abajo).

## Instalación

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Completa `.env` (nunca lo subas a git):

| Variable | Para qué |
|---|---|
| `GOOGLE_API_KEY` | Clave de Google AI Studio |
| `MODELO` | Modelo de Gemini (`gemini-3.5-flash-lite`) |
| `TELEGRAM_TOKEN` | Token de BotFather (vacío hasta conectar Telegram) |
| `TELEGRAM_SECRET` | Secreto que Telegram envía en cada webhook |
| `PUBLIC_URL` | URL https pública (vacía hasta Heroku) |

## Correr el router en local

```bash
python main.py router "¿tienen la polera azul en talla M?"
python main.py router "mi pedido 4521 llegó roto" --saltos
python main.py router --diagrama
```

`--saltos` muestra los nodos recorridos y el motivo; `--diagrama` imprime el Mermaid sin ejecutar.

## Levantar la API

```bash
uvicorn api.app:app --reload --port 8000
```

- Swagger (se puede probar todo): http://localhost:8000/docs
- Salud: `curl http://localhost:8000/health`
- Chat:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "cliente-123", "texto": "¿tienen la polera azul en talla M?"}'
```

Respuesta: `{"ruta": "preventa", "motivo": "...", "respuesta": "..."}`

La carpeta `bruno/` es una colección de [Bruno](https://www.usebruno.com/) (entornos `local` y `heroku`, variable `baseUrl`).

## Pruebas

```bash
pytest                          # exige al menos 13 de 15 aciertos (el modelo no es determinista)
python scripts/test_router.py   # tabla con cada caso, aciertos y fallados
```

Los casos están en `tests/casos_router.json`. Las pruebas llaman al modelo real, así que necesitan `GOOGLE_API_KEY`.

## Desplegar en Heroku

Ya están `Procfile`, `.python-version` (`3.12`) y `requirements.txt`. Mantén este último actualizado con `pip freeze > requirements.txt`.

```bash
heroku login
heroku create NOMBRE-DE-TU-APP
heroku config:set GOOGLE_API_KEY=... MODELO=gemini-3.5-flash-lite TELEGRAM_SECRET=un-secreto-largo
git push heroku main
heroku config:set PUBLIC_URL=https://NOMBRE-DE-TU-APP.herokuapp.com
curl https://NOMBRE-DE-TU-APP.herokuapp.com/health
```

Si tu rama local no es `main`, usa `git push heroku TU_RAMA:main`.

## Conectar Telegram

1. En Telegram habla con **@BotFather**, ejecuta `/newbot` y copia el token a `TELEGRAM_TOKEN` (local y en `heroku config:set`).
2. Con la API desplegada, registra el webhook (Telegram enviará `TELEGRAM_SECRET` en la cabecera `X-Telegram-Bot-Api-Secret-Token`):

```bash
curl -X POST "https://api.telegram.org/botTU_TELEGRAM_TOKEN/setWebhook" \
  -d "url=https://NOMBRE-DE-TU-APP.herokuapp.com/telegram" \
  -d "secret_token=TU_TELEGRAM_SECRET"
```

3. Comprueba con `curl "https://api.telegram.org/botTU_TELEGRAM_TOKEN/getWebhookInfo"`.

> **Estado actual:** `POST /telegram` solo recibe el JSON y responde `{"ok": true}`. Todavía no verifica el secreto ni responde al usuario con el router; eso falta implementarlo.