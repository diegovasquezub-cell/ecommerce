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

## Telegram

El bot usa solo `httpx` (sin librerías de bot). Telegram llama a `POST /telegram` con cada mensaje; la API verifica la cabecera `X-Telegram-Bot-Api-Secret-Token` (403 si no coincide con `TELEGRAM_SECRET`), pasa el texto por el router (`thread_id` = `chat_id`) y responde con `sendMessage`. Siempre contesta 200 a Telegram y envía la respuesta en segundo plano. Los updates sin texto se ignoran.

**Antes:** crea el bot con **@BotFather** (`/newbot`), copia el token a `TELEGRAM_TOKEN` en `.env`, elige un `TELEGRAM_SECRET` y pon en `PUBLIC_URL` la URL https de Heroku.

1. Variables en Heroku:
   ```bash
   heroku config:set TELEGRAM_TOKEN=tu_token TELEGRAM_SECRET=tu_secreto
   ```
   (con Heroku conectado a GitHub también puedes ponerlas en Settings → Config Vars).
2. Commit y push (GitHub despliega a Heroku; si no tienes auto-deploy, haz Deploy Branch):
   ```bash
   git add .
   git commit -m "telegram webhook"
   git push origin main
   git push heroku main   # solo si usas el remoto heroku
   ```
3. Registrar el webhook y confirmar (con `PUBLIC_URL` de Heroku en `.env`):
   ```bash
   python scripts/set_webhook.py
   python scripts/webhook_info.py
   ```
   En `webhook_info` debe verse `url` = `PUBLIC_URL/telegram`, `pending_update_count: 0` y sin `last_error_message`.
4. Escribe al bot estos 6 mensajes y mira en `heroku logs --tail` la línea `telegram chat_id=... ruta=...` de cada uno:
   - "¿tienen la polera azul en talla M?" → preventa
   - "mi pedido 4521 llegó roto" → postventa
   - "hola" → generica
   - "¿cuánto cuesta el envío a Valparaíso?" → preventa
   - "quiero devolver unas zapatillas" → postventa
   - "¿qué hora es en Tokio?" → generica
5. Si no responde, revisa:
   - El webhook apunta a `https://.../telegram` (`webhook_info.py`; Telegram exige https).
   - El secreto es el mismo en Heroku y al ejecutar `set_webhook.py` (si no, los logs muestran 403 en `/telegram`; vuelve a correr `set_webhook.py`).
   - El token es correcto (`last_error_message` o errores de `sendMessage` en los logs).
   - La app arrancó: `https://TU-URL/health`.

**Probar antes de desplegar (opcional):**
```bash
uvicorn api.app:app --port 8000
cloudflared tunnel --url http://localhost:8000
```
Pon la URL `https://...trycloudflare.com` que muestra cloudflared como `PUBLIC_URL`, ejecuta `python scripts/set_webhook.py` y escribe al bot. Al terminar, vuelve a poner la URL de Heroku y repite `set_webhook.py`.