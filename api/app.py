import hmac
import logging
import os
from contextlib import asynccontextmanager
from typing import Literal

import httpx
import truststore
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

truststore.inject_into_ssl()  # usa los certificados de Windows (proxy/antivirus con SSL propio)
load_dotenv()

from src.router.graph import build_graph  # noqa: E402

log = logging.getLogger("api")
# httpx registra la URL de cada request y la de Telegram lleva el token: no loguearla
logging.getLogger("httpx").setLevel(logging.WARNING)

DESCRIPCION = """
API del chat de un ecommerce. Un **router** con IA lee el mensaje del cliente y lo
envía a uno de tres agentes:

* **preventa**: intención de compra, productos, precios, tallas, stock, promociones y formas de pago.
* **postventa**: reclamos, seguimiento de pedidos, devoluciones, cambios y garantías.
* **generica**: todo lo que no tiene que ver con la tienda, o saludos sin pedido.

La conversación se recuerda por `user_id`.
"""

TAGS = [
    {"name": "salud", "description": "Estado del servicio."},
    {"name": "chat", "description": "Conversación con el router del ecommerce."},
    {"name": "telegram", "description": "Webhook de Telegram."},
]


class ChatRequest(BaseModel):
    user_id: str = Field(
        ..., min_length=1, description="Identificador del usuario; define la memoria de la conversación.",
        examples=["cliente-123"],
    )
    texto: str = Field(
        ..., min_length=1, description="Mensaje del cliente.",
        examples=["¿tienen la polera azul en talla M?"],
    )


class ChatResponse(BaseModel):
    ruta: Literal["preventa", "postventa", "generica"] = Field(
        description="Agente al que se enrutó el mensaje.", examples=["preventa"]
    )
    motivo: str = Field(
        description="Una frase con la razón de la ruta.",
        examples=["El cliente pregunta por disponibilidad y talla antes de comprar."],
    )
    respuesta: str = Field(
        description="Respuesta del agente elegido.",
        examples=["Soy el agente de preventa. Recibí: ¿tienen la polera azul en talla M?. Pronto podré ayudarte con productos y compras."],
    )


class Error(BaseModel):
    detail: str = Field(description="Descripción del error.", examples=["El servicio de IA no está disponible. Intenta de nuevo."])


class Salud(BaseModel):
    ok: bool = Field(description="True si el servicio está arriba.", examples=[True])
    modelo: str | None = Field(description="Modelo de IA configurado.", examples=["gemini-3.5-flash-lite"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = build_graph()  # se compila una sola vez al arrancar
    yield


app = FastAPI(
    title="Ecommerce Router API",
    version="0.1.0",
    description=DESCRIPCION,
    openapi_tags=TAGS,
    lifespan=lifespan,
)


@app.get("/health", response_model=Salud, tags=["salud"], summary="Estado del servicio")
def health():
    return {"ok": True, "modelo": os.getenv("MODELO")}


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Enviar un mensaje al router",
    responses={
        200: {"description": "Mensaje enrutado; trae la ruta, el motivo y la respuesta del agente."},
        422: {"description": "Body inválido: falta `user_id` o `texto`, o están vacíos."},
        502: {"model": Error, "description": "El modelo de IA falló; reintenta más tarde."},
    },
)
def chat(body: ChatRequest, request: Request):
    config = {"configurable": {"thread_id": body.user_id}}
    try:
        r = request.app.state.graph.invoke(
            {"mensaje": body.texto, "messages": [("user", body.texto)]}, config
        )
    except Exception:
        log.exception("Falló el grafo para user_id=%s", body.user_id)
        raise HTTPException(status_code=502, detail="El servicio de IA no está disponible. Intenta de nuevo.")
    return {"ruta": r["ruta"], "motivo": r["motivo"], "respuesta": r["respuesta"]}


def _responder_telegram(graph, chat_id: int, texto: str) -> None:
    """Corre el router y envía la respuesta al usuario. Nunca lanza: Telegram ya recibió 200."""
    try:
        config = {"configurable": {"thread_id": str(chat_id)}}
        r = graph.invoke({"mensaje": texto, "messages": [("user", texto)]}, config)
        log.info("telegram chat_id=%s ruta=%s", chat_id, r["ruta"])
        respuesta = r["respuesta"]
    except Exception:
        log.exception("Falló el grafo para chat_id=%s", chat_id)
        respuesta = "Tuve un problema para procesar tu mensaje. Intenta de nuevo en un momento."
    try:
        httpx.post(
            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage",
            json={"chat_id": chat_id, "text": respuesta},
            timeout=15,
        ).raise_for_status()
    except Exception as e:
        # no loguear la excepción completa: su mensaje incluye la URL con el token
        log.error("No se pudo enviar el mensaje a chat_id=%s (%s)", chat_id, type(e).__name__)


@app.post("/telegram", tags=["telegram"], include_in_schema=False)
async def telegram(request: Request, background: BackgroundTasks):
    secreto = os.getenv("TELEGRAM_SECRET") or ""
    recibido = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not secreto or not hmac.compare_digest(recibido, secreto):
        raise HTTPException(status_code=403, detail="Forbidden")

    update = await request.json()
    mensaje = update.get("message") or {}
    texto = mensaje.get("text")
    chat_id = (mensaje.get("chat") or {}).get("id")
    if texto and chat_id is not None:
        background.add_task(_responder_telegram, request.app.state.graph, chat_id, texto)
    return {"ok": True}