"""Corre los casos de tests/casos_router.json contra el router y muestra una tabla.

Uso (desde la raíz): python scripts/test_router.py
"""
import json
import sys
import uuid
import warnings
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
warnings.filterwarnings("ignore")

import truststore  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

truststore.inject_into_ssl()
load_dotenv(RAIZ / ".env")

from src.router.graph import build_graph  # noqa: E402


def main():
    casos = json.loads((RAIZ / "tests" / "casos_router.json").read_text(encoding="utf-8"))
    graph = build_graph()
    filas, fallados = [], []

    for c in casos:
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        r = graph.invoke({"mensaje": c["mensaje"], "messages": [("user", c["mensaje"])]}, config)
        ok = r["ruta"] == c["esperado"]
        filas.append((c["mensaje"], c["esperado"], r["ruta"], "✔" if ok else "✘", r["motivo"]))
        if not ok:
            fallados.append(c["mensaje"])

    ancho = max(len(f[0]) for f in filas)
    print(f"{'MENSAJE':<{ancho}} | {'ESPERADO':<9} | {'OBTENIDO':<9} |   | MOTIVO")
    print("-" * (ancho + 60))
    for m, e, o, s, mot in filas:
        print(f"{m:<{ancho}} | {e:<9} | {o:<9} | {s} | {mot}")

    aciertos = len(casos) - len(fallados)
    print(f"\nAciertos: {aciertos}/{len(casos)} ({aciertos / len(casos):.0%})")
    if fallados:
        print("Fallados:")
        for m in fallados:
            print(f"  - {m}")


if __name__ == "__main__":
    main()