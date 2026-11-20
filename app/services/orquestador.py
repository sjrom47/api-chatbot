import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


def definir_tool() -> dict:
    return {
        "type": "function",
        "function": {
            "name": NOMBRE_TOOL,
            "description": "Calcula la probabilidad de impago de una solicitud de préstamo.",
            "parameters": PrestamoEntrada.model_json_schema(),
        },
    }


def ejecutar_tool(nombre, argumentos_json) -> dict:
    if nombre != NOMBRE_TOOL:
        return {"ok": False, "error": f"Herramienta desconocida: {nombre}"}

    try:
        entrada = PrestamoEntrada.model_validate_json(argumentos_json)
    except ValidationError as error:
        return {"ok": False, "error": str(error)}

    try:
        salida = predecir(entrada)
    except Exception as error:
        return {"ok": False, "error": f"No se pudo calcular el riesgo: {error}"}
    return {"ok": True, **salida.model_dump()}


def procesar_llamada(llamada):
    funcion = llamada["function"]
    resultado = ejecutar_tool(funcion["name"], funcion["arguments"])

    herramienta = HerramientaUsada(
        nombre=funcion["name"],
        argumentos=leer_argumentos(funcion["arguments"]),
        resultado=resultado,
    )
    mensaje = {
        "role": "tool",
        "tool_call_id": llamada["id"],
        "content": json.dumps(resultado, ensure_ascii=False),
    }
    return herramienta, mensaje


def responder(mensajes, llm) -> ChatSalida:
    historial = [{"role": "system", "content": SISTEMA}]
    historial.extend(mensaje.model_dump() for mensaje in mensajes)
    herramientas = [definir_tool()]
    ultima_herramienta = None

    for _ in range(MAX_VUELTAS):
        respuesta = llm.completar(historial, herramientas)
        llamadas = respuesta.get("tool_calls")
        if not llamadas:
            return ChatSalida(
                respuesta=respuesta.get("content") or "No he podido generar una respuesta.",
                herramienta=ultima_herramienta,
            )

        historial.append(respuesta)
        for llamada in llamadas:
            ultima_herramienta, mensaje = procesar_llamada(llamada)
            historial.append(mensaje)

    return ChatSalida(
        respuesta="No he podido completar la solicitud en el máximo de intentos permitidos.",
        herramienta=ultima_herramienta,
    )
