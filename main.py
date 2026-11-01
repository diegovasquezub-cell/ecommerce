import argparse
import importlib
import uuid

import truststore
from dotenv import load_dotenv

truststore.inject_into_ssl()  # usa los certificados de Windows (proxy/antivirus con SSL propio)


def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("agente")
    p.add_argument("mensaje", nargs="?", default="")
    p.add_argument("--saltos", action="store_true", help="imprime los nodos recorridos")
    p.add_argument("--diagrama", action="store_true", help="imprime el Mermaid sin ejecutar")
    p.add_argument("--thread", default=None, help="thread_id de la conversación")
    a = p.parse_args()

    graph = importlib.import_module(f"src.{a.agente}.graph").build_graph()

    if a.diagrama:
        print(graph.get_graph().draw_mermaid())
        return

    config = {"configurable": {"thread_id": a.thread or str(uuid.uuid4())}}
    entrada = {"mensaje": a.mensaje, "messages": [("user", a.mensaje)]}

    saltos = []
    for paso in graph.stream(entrada, config, stream_mode="updates"):
        for nodo, salida in paso.items():
            saltos.append(nodo)
            if a.saltos and nodo == "router":
                print(f"[router] motivo: {salida.get('motivo')}")
    if a.saltos:
        print(" → ".join(saltos))

    final = graph.get_state(config).values
    print(f"ruta: {final.get('ruta')}")
    print(f"motivo: {final.get('motivo')}")
    print(f"respuesta: {final.get('respuesta')}")


if __name__ == "__main__":
    main()