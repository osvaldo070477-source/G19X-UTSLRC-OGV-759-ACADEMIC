"""Verificación estática de la interfaz (sin navegador).
Comprueba que cada id usado por public/app.js exista en public/index.html,
que cada data-tab tenga su sección y que cada data-goto apunte a una
sección válida. Uso:  python scripts/check_ui.py
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = open(os.path.join(BASE, "public", "index.html"), encoding="utf-8").read()
js = open(os.path.join(BASE, "public", "app.js"), encoding="utf-8").read()
css = open(os.path.join(BASE, "public", "styles.css"), encoding="utf-8").read()

fails = []


def check(name, cond):
    print(("OK  " if cond else "FALLO ") + name)
    if not cond:
        fails.append(name)


html_ids = set(re.findall(r'id="([A-Za-z]+)"', html))
js_ids = set(re.findall(r'\$\("([A-Za-z]+)"\)', js))
DYNAMIC = {"agApprove", "agReject", "agRevComment"}  # creados por JS al pintar revisiones
missing = sorted(i for i in js_ids if i not in html_ids and i not in DYNAMIC)
check(f"IDs de JS existen en HTML ({len(js_ids)} usados)", not missing)
for m in missing:
    print("   falta: " + m)

sections = set(re.findall(r'id="tab-([a-z]+)"', html))
check("data-tab del menú tiene sección", all(t in sections for t in re.findall(r'data-tab="([a-z]+)"', html)))
gotos = set(re.findall(r"data-goto='([a-z]+)'", js)) | set(re.findall(r'data-goto="([a-z]+)"', html))
check("data-goto apunta a secciones válidas: " + ",".join(sorted(gotos)), all(g in sections for g in gotos))
css_nomotion = re.sub(r"@media\s*\(prefers-reduced-motion[^}]+\{[^}]+\}", "", css)
check("sin !important salvo [hidden] y reduced-motion", css_nomotion.count("!important") == 1)
check("sin emojis en la interfaz", not re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]", html + js))

used = set()
for m in re.findall(r'class="([^"]+)"', html):
    used.update(m.split())
for m in re.findall(r"class='([^']+)'", js):
    used.update(m.split())
defined = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
IGNORE_CLS = {"badge", "alta", "media", "baja", "estado", "ia", "det",
              "done", "active", "idle", "muted", "small"}
missing_cls = sorted(u for u in used
                     if u not in defined and u not in IGNORE_CLS and re.fullmatch(r"[A-Za-z][\w-]*", u or ""))
check("clases usadas existen en CSS (%d)" % len(used), not missing_cls)
for m in missing_cls:
    print("   falta: ." + m)

print("RESULTADO:", "TODO OK" if not fails else f"{len(fails)} FALLOS")
sys.exit(0 if not fails else 1)
