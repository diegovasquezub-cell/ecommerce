import json
import uuid
from pathlib import Path

import pytest
import truststore
from dotenv import load_dotenv

truststore.inject_into_ssl()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.router.graph import build_graph  # noqa: E402

CASOS = json.loads((Path(__file__).parent / "casos_router.json").read_text(encoding="utf-8"))
MINIMO = 13  # el modelo no es determinista: se tolera algún fallo


@pytest.fixture(scope="module")
def graph():
    return build_graph()


@pytest.mark.parametrize("minimo", [MINIMO])
def test_router_acierta_al_menos_13_de_15(graph, minimo):
    fallados = []
    for c in CASOS:
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        r = graph.invoke({"mensaje": c["mensaje"], "messages": [("user", c["mensaje"])]}, config)
        if r["ruta"] != c["esperado"]:
            fallados.append(f"{c['mensaje']!r}: esperado={c['esperado']} obtenido={r['ruta']}")
    aciertos = len(CASOS) - len(fallados)
    assert aciertos >= minimo, f"{aciertos}/{len(CASOS)} aciertos. Fallados:\n" + "\n".join(fallados)