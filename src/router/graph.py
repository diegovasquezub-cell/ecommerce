import os
from typing import Annotated, Literal

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from . import prompts


class Decision(BaseModel):
    ruta: Literal["preventa", "postventa", "generica"] = Field(
        description="A qué agente va el mensaje."
    )
    motivo: str = Field(description="Una frase: por qué esa ruta.")


class Estado(TypedDict, total=False):
    mensaje: str
    ruta: str
    motivo: str
    respuesta: str
    messages: Annotated[list, add_messages]


def router(estado: Estado) -> dict:
    llm = ChatGoogleGenerativeAI(model=os.environ["MODELO"], temperature=0)
    decision = llm.with_structured_output(Decision).invoke(
        [("system", prompts.PROMPT_ROUTER), *estado["messages"]]
    )
    return {"ruta": decision.ruta, "motivo": decision.motivo}


def _responder(texto: str) -> dict:
    return {"respuesta": texto, "messages": [AIMessage(content=texto)]}


def agente_preventa(estado: Estado) -> dict:
    return _responder(prompts.PROMPT_PREVENTA.format(mensaje=estado["mensaje"]))


def agente_postventa(estado: Estado) -> dict:
    return _responder(prompts.PROMPT_POSTVENTA.format(mensaje=estado["mensaje"]))


def respuesta_generica(estado: Estado) -> dict:
    return _responder(prompts.RESPUESTA_GENERICA)


NODO_POR_RUTA = {
    "preventa": "agente_preventa",
    "postventa": "agente_postventa",
    "generica": "respuesta_generica",
}


def build_graph():
    g = StateGraph(Estado)
    g.add_node("router", router)
    g.add_node("agente_preventa", agente_preventa)
    g.add_node("agente_postventa", agente_postventa)
    g.add_node("respuesta_generica", respuesta_generica)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", lambda e: e["ruta"], NODO_POR_RUTA)
    for nodo in NODO_POR_RUTA.values():
        g.add_edge(nodo, END)
    return g.compile(checkpointer=MemorySaver())