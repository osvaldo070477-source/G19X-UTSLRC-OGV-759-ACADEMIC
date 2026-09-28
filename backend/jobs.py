"""Trabajos agentic en segundo plano (NEXO).

Estados: pendiente, en_ejecucion, esperando_revision, completado,
fallido, cancelado, interrumpido. La API responde al instante con el
identificador; el trabajo avanza en un hilo y se consulta por progreso.
Cancelación entre pasos; reintento explícito que crea un trabajo nuevo
(nunca duplica eventos del original).
"""

import datetime
import threading
import time

from agents import AwaitingReview, JobHalt, drive

TERMINAL = ("completado", "fallido", "cancelado", "interrumpido")


def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def new_job(params, provider_name, model, stub):
    return {"id": None, "estado": "pendiente", "params": params,
            "proveedor": provider_name, "modelo": model, "stub": stub,
            "creado_en": now_iso(), "iniciado_en": None, "terminado_en": None,
            "etapas": [], "herramientas": [], "revisiones": [],
            "uso": {"prompt": 0, "completion": 0, "total": 0, "llamadas_modelo": 0},
            "tool_calls_total": 0, "error": None, "codigo_error": None,
            "run_id": None, "catalogo": None, "determinista": None,
            "recomendaciones_draft": None, "resume_stage": "catalogo",
            "revision_aprobada": False, "_cancel": False}


class MemoryStore:
    """Persistencia temporal (modos sin MySQL): se pierde al reiniciar."""

    def __init__(self):
        self.jobs, self.seq = {}, [0]

    def create(self, job):
        self.seq[0] += 1
        job["id"] = self.seq[0]
        self.jobs[job["id"]] = job
        return job["id"]

    def update(self, job):
        self.jobs[job["id"]] = job

    def get(self, job_id):
        return self.jobs.get(job_id)

    def list(self, limit=20):
        return [self.jobs[k] for k in sorted(self.jobs, reverse=True)[:limit]]

    # API compatible con el almacén MySQL (sin operación real)
    def append_etapa(self, job, evento):
        pass

    def append_herramienta(self, job, llamada):
        pass

    def add_revision(self, job, revision):
        pass

    def save_recommendations(self, job, recs):
        pass

    def mark_interrupted_on_boot(self):
        return 0


class MysqlStore:
    """Persistencia real en nexo_app (ver sql/05_agentic.sql)."""

    def __init__(self, cfg):
        self.cfg = cfg

    def _connect(self):
        try:
            import mysql.connector  # type: ignore
        except ImportError as e:
            raise RuntimeError("mysql-connector-python no está instalado.") from e
        c = self.cfg
        return mysql.connector.connect(host=c["host"], port=c["port"], user=c["user"],
                                       password=c["password"], database="nexo_app")

    def create(self, job):
        import json as _json
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO agent_jobs (estado, modo_fuente, proveedor, modelo, es_prueba, params_json) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                ("pendiente", job["params"].get("fuente", "muestra"), job["proveedor"],
                 job["modelo"], 1 if job["stub"] else 0, _json.dumps(job["params"], ensure_ascii=False)))
            job["id"] = cur.lastrowid
            conn.commit()
            return job["id"]
        finally:
            conn.close()

    def update(self, job):
        import json as _json
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE agent_jobs SET estado=%s, iniciado_en=%s, terminado_en=%s, run_id=%s, "
                "error=%s, codigo_error=%s, uso_json=%s, resumen_json=%s WHERE id=%s",
                (job["estado"], job["iniciado_en"], job["terminado_en"], job["run_id"],
                 (job["error"] or "")[:500], job["codigo_error"],
                 _json.dumps(job["uso"], ensure_ascii=False),
                 _json.dumps({"determinista": job.get("determinista"),
                              "catalogo": job.get("catalogo")}, ensure_ascii=False)[:4000],
                 job["id"]))
            conn.commit()
        finally:
            conn.close()

    def get(self, job_id):
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM agent_jobs WHERE id=%s", (job_id,))
            row = cur.fetchone()
            if not row:
                return None
            cur.execute("SELECT etapa, evento, resumen, creado_en FROM agent_steps WHERE job_id=%s ORDER BY id", (job_id,))
            etapas = cur.fetchall()
            cur.execute("SELECT agente, herramienta, argumentos_json, ok, resumen, ms FROM tool_calls "
                        "WHERE job_id=%s ORDER BY id", (job_id,))
            herramientas = cur.fetchall()
            cur.execute("SELECT id, motivo, estado, comentario, creado_en FROM reviews WHERE job_id=%s ORDER BY id", (job_id,))
            revisiones = cur.fetchall()
            cur.execute("SELECT tabla, columna, regla, problema, accion, prioridad, justificacion, "
                        "limitaciones, revision_humana, estado FROM recommendations WHERE job_id=%s ORDER BY id", (job_id,))
            recs = cur.fetchall()
            import json as _json
            resumen = _json.loads(row["resumen_json"] or "{}") if row["resumen_json"] else {}
            return {"id": row["id"], "estado": row["estado"], "params": _json.loads(row["params_json"] or "{}"),
                    "proveedor": row["proveedor"], "modelo": row["modelo"], "stub": bool(row["es_prueba"]),
                    "creado_en": str(row["creado_en"]), "iniciado_en": str(row["iniciado_en"] or ""),
                    "terminado_en": str(row["terminado_en"] or ""), "etapas": etapas,
                    "herramientas": herramientas, "revisiones": revisiones, "recomendaciones": recs,
                    "uso": _json.loads(row["uso_json"] or "{}"), "error": row["error"],
                    "codigo_error": row["codigo_error"], "run_id": row["run_id"],
                    "determinista": resumen.get("determinista"), "catalogo": resumen.get("catalogo")}
        finally:
            conn.close()

    def list(self, limit=20):
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, estado, modo_fuente, proveedor, modelo, es_prueba, run_id, "
                        "codigo_error, creado_en FROM agent_jobs ORDER BY id DESC LIMIT %s", (limit,))
            return cur.fetchall()
        finally:
            conn.close()

    def append_etapa(self, job, evento):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO agent_steps (job_id, etapa, evento, resumen) VALUES (%s,%s,%s,%s)",
                        (job["id"], evento.get("etapa", ""), evento.get("evento", ""),
                         (evento.get("resumen", "") or "")[:500]))
            conn.commit()
        finally:
            conn.close()

    def append_herramienta(self, job, llamada):
        import json as _json
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO tool_calls (job_id, agente, herramienta, argumentos_json, ok, resumen, ms) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (job["id"], llamada.get("agente", ""), llamada.get("herramienta", ""),
                         _json.dumps(llamada.get("argumentos", {}), ensure_ascii=False)[:2000],
                         1 if llamada.get("ok") else 0, (llamada.get("resumen", "") or "")[:1000],
                         llamada.get("ms", 0)))
            conn.commit()
        finally:
            conn.close()

    def add_revision(self, job, revision):
        import json as _json
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO reviews (job_id, motivo, contexto_json, estado) VALUES (%s,%s,%s,'pendiente')",
                        (job["id"], revision["motivo"][:500],
                         _json.dumps(revision.get("contexto", {}), ensure_ascii=False)[:4000]))
            revision["id"] = cur.lastrowid
            conn.commit()
            return revision["id"]
        finally:
            conn.close()

    def resolve_revision(self, job, revision_id, decision, comentario):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE reviews SET estado=%s, comentario=%s, respondido_en=NOW() "
                        "WHERE id=%s AND job_id=%s AND estado='pendiente'",
                        ("aprobada" if decision == "approve" else "rechazada",
                         (comentario or "")[:1000], revision_id, job["id"]))
            ok = cur.rowcount == 1
            conn.commit()
            return ok
        finally:
            conn.close()

    def save_recommendations(self, job, recs):
        conn = self._connect()
        try:
            cur = conn.cursor()
            conn.start_transaction()
            for r in recs:
                cur.execute(
                    "INSERT INTO recommendations (job_id, tabla, columna, regla, problema, accion, "
                    "prioridad, justificacion, limitaciones, revision_humana, estado) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pendiente')",
                    (job["id"], r["ref_hallazgo"].split(".")[0], r["ref_hallazgo"].split(".")[1],
                     r["ref_hallazgo"].split(".")[2], r["problema"][:500], r["accion"][:500],
                     r["prioridad"], r["justificacion"][:500], str(r.get("limitaciones", ""))[:500],
                     1 if r["revision_humana"] else 0))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def mark_interrupted_on_boot(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE agent_jobs SET estado='interrumpido', terminado_en=NOW(), "
                        "codigo_error='interrumpido', error='Servicio reiniciado durante la ejecución. "
                        "Puede reintentarse explícitamente.' "
                        "WHERE estado IN ('en_ejecucion','esperando_revision')")
            n = cur.rowcount
            conn.commit()
            return n
        finally:
            conn.close()


class Manager:
    """Coordina hilos, cancelación, revisión y reintento."""

    def __init__(self, store, provider_factory, cfg, hooks):
        self.store = store
        self.provider_factory = provider_factory
        self.cfg = cfg
        self.hooks = hooks  # fetch_tables, metadata, last_run, save_run
        self.lock = threading.Lock()
        self.live = {}  # job_id -> job vivo en memoria

    # ---------- inicio ----------
    def start(self, params):
        fuente = params.get("fuente", "muestra")
        if fuente not in ("muestra", "origen"):
            raise ValueError("Fuente inválida: usa muestra u origen.")
        if fuente == "origen" and not self.hooks.get("mysql_ok", lambda: False)():
            raise ValueError("Fuente 'origen' no disponible: el servicio corre sin MySQL (--demo).")
        provider = self.provider_factory()
        stub = bool(getattr(provider, "name", "") == "stub" or
                    provider.__class__.__name__ == "StubProvider")
        if not stub and not self.cfg.get("api_key"):
            raise ValueError("IA sin configurar: falta NEXO_AI_API_KEY en el .env del servidor.")
        job = new_job({"fuente": fuente, "pedir_revision": bool(params.get("pedir_revision", False))},
                      provider.name if hasattr(provider, "name") else "stub",
                      self.cfg.get("model", ""), stub)
        job["estado"] = "en_ejecucion"
        job["iniciado_en"] = now_iso()
        self.store.create(job)
        job["_resume_event"] = threading.Event()
        job["_thread"] = None
        job["_provider"] = provider
        with self.lock:
            self.live[job["id"]] = job
        t = threading.Thread(target=self._run, args=(job, provider), daemon=True)
        job["_thread"] = t
        t.start()
        return job["id"]

    def _svc(self, job, provider):
        cfg, hooks = self.cfg, self.hooks
        tables = hooks["fetch_tables"](job["params"]["fuente"])
        deadline = time.time() + cfg["job_timeout_s"]

        def throw_if_cancelled():
            if job["_cancel"]:
                raise JobHalt("cancelado", "cancelado", "Cancelado por el operador entre pasos.")

        def check_deadline():
            if time.time() > deadline:
                raise JobHalt("fallido", "tiempo_agotado", "Se agotó el tiempo máximo del trabajo.")

        def add_usage(u):
            if not u:
                return
            job["uso"]["prompt"] += u.get("prompt", 0)
            job["uso"]["completion"] += u.get("completion", 0)
            job["uso"]["total"] += u.get("total", 0)
            job["uso"]["llamadas_modelo"] += 1

        def emit(kind, data):
            if kind == "etapa":
                job["etapas"].append({**data, "en": now_iso()})
                self.store.append_etapa(job, data)
            elif kind == "herramienta":
                job["herramientas"].append({**data, "en": now_iso()})
                self.store.append_herramienta(job, data)
            self.store.update(job)

        tool_ctx = {"tables": tables, "metadata": hooks["metadata"](),
                    "last_run": hooks["last_run"](), "redact": cfg.get("redact", True),
                    "max_rows": cfg.get("max_rows_tool", 200)}
        return {"provider": provider, "cfg": cfg, "tool_ctx": tool_ctx,
                "save_run": hooks["save_run"], "throw_if_cancelled": throw_if_cancelled,
                "check_deadline": check_deadline, "add_usage": add_usage, "emit": emit,
                "save_recommendations": lambda j: self._save_recs(j)}

    def _save_recs(self, job):
        self.store.save_recommendations(job, job["recomendaciones_draft"])
        job["recomendaciones"] = job["recomendaciones_draft"]

    def _run(self, job, provider):
        try:
            svc = self._svc(job, provider)
            drive(job, svc, job.get("resume_stage") or "catalogo")
            job["estado"] = "completado"
            job["terminado_en"] = now_iso()
        except AwaitingReview as r:
            job["estado"] = "esperando_revision"
            rev = {"motivo": r.mensaje, "contexto": getattr(r, "contexto", {}), "estado": "pendiente",
                   "creado_en": now_iso()}
            job["revisiones"].append(rev)
            self.store.add_revision(job, rev)
        except JobHalt as h:
            job["estado"] = h.estado
            job["codigo_error"] = h.codigo
            job["error"] = h.mensaje
            job["terminado_en"] = now_iso()
        except Exception as e:  # noqa: BLE001 - un fallo inesperado también queda registrado
            job["estado"] = "fallido"
            job["codigo_error"] = "interno"
            job["error"] = f"{type(e).__name__}: {e}"[:500]
            job["terminado_en"] = now_iso()
        finally:
            try:
                self.store.update(job)
            except Exception:  # noqa: BLE001, S110 - el estado en memoria ya es correcto
                pass

    # ---------- consulta ----------
    def get(self, job_id):
        with self.lock:
            job = self.live.get(job_id)
        if job is not None:
            return self._public(job)
        return self.store.get(job_id)

    def list(self, limit=20):
        with self.lock:
            live_ids = set(self.live)
        rows = self.store.list(limit)
        if isinstance(self.store, MemoryStore):
            return [self._public(self.live[k]) for k in sorted(self.live, reverse=True)[:limit]]
        out = []
        for r in rows:
            out.append(r if r["id"] not in live_ids else self._public(self.live[r["id"]]))
        return out

    @staticmethod
    def _public(job):
        return {k: v for k, v in job.items() if not k.startswith("_")}

    # ---------- cancelación ----------
    def cancel(self, job_id):
        with self.lock:
            job = self.live.get(job_id)
        if job is None:
            raise LookupError("Trabajo no encontrado en esta sesión.")
        if job["estado"] not in ("en_ejecucion", "esperando_revision"):
            raise ValueError(f"No se puede cancelar en estado {job['estado']}.")
        job["_cancel"] = True
        job["_resume_event"].set()
        if job["estado"] == "esperando_revision":
            job["estado"] = "cancelado"
            job["codigo_error"] = "cancelado"
            job["error"] = "Cancelado por el operador durante la revisión."
            job["terminado_en"] = now_iso()
            self.store.update(job)
        return True

    # ---------- revisión humana ----------
    def review(self, job_id, decision, comentario=""):
        if decision not in ("approve", "reject"):
            raise ValueError("Decisión inválida: usa approve o reject.")
        if not isinstance(comentario, str) or len(comentario) > 1000:
            raise ValueError("El comentario debe tener como máximo 1000 caracteres.")
        with self.lock:
            job = self.live.get(job_id)
        if job is None:
            raise LookupError("Trabajo no encontrado en esta sesión.")
        if job["estado"] != "esperando_revision":
            raise ValueError(f"Reanudación incompatible: el trabajo está {job['estado']}.")
        rev = job["revisiones"][-1]
        rev["estado"] = "aprobada" if decision == "approve" else "rechazada"
        rev["comentario"] = comentario
        if hasattr(self.store, "resolve_revision"):
            self.store.resolve_revision(job, rev.get("id", 0), decision, comentario)
        if decision == "reject":
            job["estado"] = "cancelado"
            job["codigo_error"] = "revision_rechazada"
            job["error"] = "Revisión humana rechazada por el operador."
            job["terminado_en"] = now_iso()
            self.store.update(job)
            return "cancelado"
        job["revision_aprobada"] = True
        job["estado"] = "en_ejecucion"
        self.store.update(job)
        t = threading.Thread(target=self._run, args=(job, job["_provider"]), daemon=True)
        t.start()
        return "reanudado"

    # ---------- reintento ----------
    def retry(self, job_id):
        base = self.get(job_id)
        if base is None:
            raise LookupError("Trabajo no encontrado.")
        if base["estado"] not in TERMINAL:
            raise ValueError("Solo se reintentan trabajos terminados.")
        return self.start(dict(base.get("params", {})))
