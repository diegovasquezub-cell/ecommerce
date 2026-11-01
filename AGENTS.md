# AGENTS.md

## Estructura de agentes
- Los agentes van en `src/{nombre_agente}/` con `graph.py`, `prompts.py` y `tools.py`.
- Cada nodo tiene su propio prompt en `prompts.py`; nada de reglas dentro de `graph.py`.
- `graph.py` debe exponer `build_graph()` que devuelve el grafo compilado.

## Ejecución
Desde la raíz: `python main.py {nombre_agente} "mensaje"`
- `--saltos`: imprime los nodos por los que pasó el grafo.
- `--diagrama`: imprime el Mermaid del grafo sin ejecutarlo.

## API
- Va en `api/app.py` (FastAPI). Se levanta con: `uvicorn api.app:app --reload --port 8000`.

## Scripts y pruebas
- Scripts sueltos en `scripts/`.
- Pruebas en `tests/` (pytest).

## Heroku
- `Procfile`: `web: uvicorn api.app:app --host 0.0.0.0 --port $PORT`
- `.python-version` con `3.12`.
- `requirements.txt` siempre actualizado (`pip freeze > requirements.txt`).

## Secretos
- Nunca valores reales en el código; todo va en `.env` (plantilla en `.env.example`).
- `.gitignore` incluye `.env`, `.venv`, `__pycache__` y `.langgraph_api`.