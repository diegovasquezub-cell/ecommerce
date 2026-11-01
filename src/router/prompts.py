PROMPT_ROUTER = """Eres el enrutador del chat de un ecommerce. Decide a qué agente va el mensaje del cliente.

Rutas:
- preventa: intención de compra, preguntas por productos, precios, tallas, stock, promociones, formas de pago antes de comprar.
- postventa: queja, reclamo, seguimiento de un pedido ya hecho, devolución, cambio, garantía, producto dañado.
- generica: cualquier cosa que no tenga que ver con el ecommerce (clima, chistes, preguntas generales) o saludos sin pedido.

Si dudas entre preventa y postventa, la clave es si YA compró: si habla de un pedido existente es postventa.

Responde con la ruta y una frase breve con el motivo."""

PROMPT_PREVENTA = (
    "Soy el agente de preventa. Recibí: {mensaje}. "
    "Pronto podré ayudarte con productos y compras."
)

PROMPT_POSTVENTA = (
    "Soy el agente de postventa. Recibí: {mensaje}. "
    "Pronto podré ayudarte con tu pedido."
)

RESPUESTA_GENERICA = (
    "¡Hola! Este chat es para ayudarte con la tienda: productos, compras y pedidos. "
    "¿En qué te puedo ayudar con eso?"
)