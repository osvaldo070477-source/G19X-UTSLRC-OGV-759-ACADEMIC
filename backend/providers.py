"""Proveedor de modelo de lenguaje desacoplado (NEXO agentic).

Interfaz: chat(messages, tools, tool_choice, json_mode) -> dict con
  content (str|None), tool_calls ([{id, name, arguments|args_error}]),
  usage ({prompt, completion, total}|None), model, stub (bool).

Adaptadores:
  - StubProvider: doble de prueba determinista. NUNCA es IA real;
    sus respuestas llevan stub:true y la interfaz lo etiqueta.
  - OpenAICompatProvider: adaptador real sobre HTTP (urllib, sin
    dependencias) contra POST {base_url}/chat/completions con
    `tools` (function calling) y `response_format` (salidas
    estructuradas). Verificado contra la referencia oficial:
    https://platform.openai.com/docs/api-reference/chat/create
    Sirve para OpenAI y para cualquier servidor compatible
    (p. ej. un modelo local con API compatible).

Las claves viajan solo en el servidor (variables de entorno) y jamás
llegan al navegador. No se realizan llamadas de pago sin que el
operador configure la clave y pulse iniciar.
"""

import json
import os
import urllib.error
import urllib.request

DEFAULT_MODEL = "gpt-4o-mini"  # modelo documentado y económico; se cambia con NEXO_AI_MODEL


class ProviderError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code  # timeout | unreachable | auth | bad_request | invalid_response | server


def ai_config_from_env(env=None):
    env = env if env is not None else os.environ
    get = lambda k, d="": (env.get(k, d) or d)
    return {
        "provider": get("NEXO_AI_PROVIDER", "stub").strip().lower(),
        "model": get("NEXO_AI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        "base_url": get("NEXO_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "api_key": get("NEXO_AI_API_KEY", ""),
        "timeout_s": int(get("NEXO_AI_TIMEOUT_S", "180") or 180),
        "max_steps": int(get("NEXO_AI_MAX_STEPS", "10") or 10),
        "max_tool_calls": int(get("NEXO_AI_MAX_TOOL_CALLS", "20") or 20),
        "max_repairs": int(get("NEXO_AI_MAX_RETRIES", "2") or 2),
        "job_timeout_s": int(get("NEXO_AI_JOB_TIMEOUT_S", "600") or 600),
        "max_rows_tool": int(get("NEXO_AI_MAX_ROWS_TOOL", "200") or 200),
        "redact": get("NEXO_AI_REDACT", "1").strip() not in ("0", "no", "false"),
    }


def provider_status(cfg=None):
    """Estado para la interfaz. Sin secretos: solo indica qué falta."""
    cfg = cfg or ai_config_from_env()
    name = cfg["provider"]
    missing = []
    if name == "openai" and not cfg["api_key"]:
        missing.append("NEXO_AI_API_KEY")
    host = cfg["base_url"].split("://", 1)[-1].split("/", 1)[0] if name == "openai" else ""
    return {
        "provider": name,
        "model": cfg["model"],
        "base_host": host,
        "stub": name != "openai",
        "configured": (name == "openai" and not missing) or name == "stub",
        "missing": missing,
        "limits": {
            "max_steps": cfg["max_steps"], "max_tool_calls": cfg["max_tool_calls"],
            "timeout_s": cfg["timeout_s"], "job_timeout_s": cfg["job_timeout_s"],
            "max_repairs": cfg["max_repairs"], "max_rows_tool": cfg["max_rows_tool"],
        },
    }


def make_provider(cfg=None):
    cfg = cfg or ai_config_from_env()
    if cfg["provider"] == "openai":
        return OpenAICompatProvider(cfg)
    return StubProvider(cfg)


class StubProvider:
    """Doble de prueba: respuestas programadas o guion por etapas, sin red.

    Sin guion responde por etapas (cataloga, sondea calidad y propone con
    plantillas) para demostrar el flujo completo. stub=True siempre:
    NUNCA es IA real y la interfaz lo etiqueta como proveedor de prueba.
    """

    name = "stub"

    def __init__(self, cfg, script=None):
        self.cfg = cfg
        self.script = list(script) if script is not None else None
        self.calls = 0

    def chat(self, messages, tools=None, tool_choice="auto", json_mode=False, timeout=None):
        self.calls += 1
        if self.script is not None:
            if not self.script:
                raise ProviderError("invalid_response", "Guion de prueba agotado.")
            item = self.script.pop(0)
            if isinstance(item, Exception):
                raise item
            out = dict(item)
            out.setdefault("usage", {"prompt": 10, "completion": 5, "total": 15})
            out["model"] = "stub"
            out["stub"] = True
            return out
        return self._stage_default(messages)

    def _tc(self, name, args):
        self.calls += 1
        return {"content": None,
                "tool_calls": [{"id": f"stub-{self.calls}", "name": name, "arguments": args}],
                "usage": {"prompt": 10, "completion": 5, "total": 15},
                "model": "stub", "stub": True}

    def _final(self, content):
        return {"content": content, "tool_calls": [],
                "usage": {"prompt": 10, "completion": 5, "total": 15},
                "model": "stub", "stub": True}

    def _stage_default(self, messages):
        import re as _re
        stage = ""
        for m in messages:
            if m.get("role") == "user" and "Objetivo de esta etapa:" in str(m.get("content", "")):
                found = _re.search(r"Objetivo de esta etapa:\s*(\w+)", str(m["content"]))
                if found:
                    stage = found.group(1)
        turns = sum(1 for m in messages
                      if m.get("role") == "user"
                      and str(m.get("content", "")).startswith("Resultado de tus llamadas"))
        nota = "Respuesta del proveedor de prueba (no es IA real)."
        if stage == "catalogo":
            if turns == 0:
                return self._tc("listar_tablas", {})
            if turns == 1:
                return self._tc("describir_tabla", {"tabla": "clientes"})
            return self._final(json.dumps({
                "nota": nota, "tablas": [
                    {"tabla": "clientes", "registros": 0, "observacion": "Resumen de prueba."},
                    {"tabla": "pedidos", "registros": 0, "observacion": "Resumen de prueba."},
                    {"tabla": "productos", "registros": 0, "observacion": "Resumen de prueba."}],
                "propuestas": []}, ensure_ascii=False))
        if stage == "calidad":
            if turns == 0:
                return self._tc("comprobar_obligatoriedad", {"tabla": "clientes", "columna": "nombre"})
            if turns == 1:
                return self._tc("comprobar_unicidad", {"tabla": "clientes", "columna": "id"})
            # Sin confirmación exacta: el orquestador usa el motor y pide revisión.
            return self._final(json.dumps(
                {"nota": nota, "hallazgos_confirmados": [], "notas": "Sondeo de prueba."},
                ensure_ascii=False))
        if stage == "recomendaciones":
            refs = _re.findall(r"\b(?:clientes|pedidos|productos)\.\w+\.(?:required|unique|email)\b",
                               " ".join(str(m.get("content", "")) for m in messages))
            recs = [{"ref_hallazgo": r, "problema": f"Hallazgo {r} (prueba).",
                     "accion": "Revisar con el responsable del dato (propuesta de prueba).",
                     "prioridad": "Media", "justificacion": "Evidencia del motor.",
                     "limitaciones": "Generada por el proveedor de prueba.",
                     "revision_humana": False} for r in dict.fromkeys(refs)]
            return self._final(json.dumps({"nota": nota, "recomendaciones": recs}, ensure_ascii=False))
        return self._final(json.dumps({"nota": nota}, ensure_ascii=False))


class OpenAICompatProvider:
    """Adaptador real contra POST {base_url}/chat/completions."""

    name = "openai"

    def __init__(self, cfg):
        self.cfg = cfg

    def chat(self, messages, tools=None, tool_choice="auto", json_mode=False, timeout=None):
        if not self.cfg["api_key"]:
            raise ProviderError("auth", "Falta NEXO_AI_API_KEY en el .env del servidor.")
        body = {"model": self.cfg["model"], "messages": messages}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            return self._post(body, timeout or self.cfg["timeout_s"])
        except ProviderError as e:
            if e.code == "bad_request" and json_mode and "response_format" in str(e).lower():
                del body["response_format"]  # el servidor no lo soporta: reintento sin él
                return self._post(body, timeout or self.cfg["timeout_s"])
            raise

    def _post(self, body, timeout):
        import time as _time
        req = urllib.request.Request(
            self.cfg["base_url"] + "/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self.cfg["api_key"]},
            method="POST")
        # Reintentos ante saturación o límite (429/503): la demanda suele ser temporal.
        last = None
        try:
            for attempt, wait in ((0, 0), (1, 15), (2, 45)):
                if wait:
                    _time.sleep(wait)
                try:
                    with urllib.request.urlopen(req, timeout=timeout) as res:
                        payload = json.loads(res.read().decode("utf-8"))
                    break
                except urllib.error.HTTPError as e:
                    try:
                        detail = json.loads(e.read().decode("utf-8", "replace"))
                        msg = detail.get("error", {}).get("message", str(detail)) if isinstance(detail, dict) else str(detail)
                    except (ValueError, UnicodeDecodeError):
                        msg = f"HTTP {e.code}"
                    if e.code in (401, 403):
                        raise ProviderError("auth", f"Clave rechazada por el proveedor: {msg}")
                    if e.code == 400:
                        raise ProviderError("bad_request", f"Petición rechazada: {msg}")
                    if e.code in (429, 503) and attempt < 2:
                        last = (e.code, msg)
                        continue
                    if e.code == 429:
                        raise ProviderError("server", f"Límite del proveedor alcanzado: {msg}")
                    raise ProviderError("server", f"Error del proveedor (HTTP {e.code}): {msg}")
        except TimeoutError:
            raise ProviderError("timeout", f"El proveedor no respondió en {timeout} s.")
        except OSError as e:
            raise ProviderError("unreachable", f"No se pudo contactar al proveedor: {e}")
        try:
            msg0 = payload["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError("invalid_response", f"Respuesta inesperada del proveedor: {e}")
        calls = []
        for tc in msg0.get("tool_calls") or []:
            fn = tc.get("function", {}) if isinstance(tc, dict) else {}
            raw = fn.get("arguments", "{}")
            try:
                args = json.loads(raw or "{}")
                err = None if isinstance(args, dict) else "los argumentos no son un objeto"
            except ValueError:
                args, err = None, "argumentos JSON inválidos"
            calls.append({"id": tc.get("id", ""), "name": fn.get("name", ""),
                          "arguments": args, "args_error": err})
        usage = payload.get("usage") or {}
        return {"content": msg0.get("content"),
                "tool_calls": calls,
                "usage": {"prompt": usage.get("prompt_tokens", 0),
                          "completion": usage.get("completion_tokens", 0),
                          "total": usage.get("total_tokens", 0)} or None,
                "model": payload.get("model", self.cfg["model"]), "stub": False}
