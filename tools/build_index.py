"""Validate every plugin and build index.json.

    python tools/build_index.py           # validate + write index.json
    python tools/build_index.py --check   # validate + fail if index.json is not up to date (CI)
    python tools/build_index.py --check --base old-index.json
                                          # + every changed plugin must have a higher version
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imageinfo import image_info  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.json"
SCHEMA = 1

# Folder → category (a plugin lives in <folder>/<plugin id>/plugin.json)
FOLDERS = {
    "games/simulation/racing": "simracing",
    "games/simulation/flight": "flightsim",
    "streaming": "streaming",
    "social": "social",
    "system": "windows",
    "apps": "apps",
    "other": "other",
}
ACTION_TYPES = {
    "hotkey", "text", "launch", "open", "command", "kill", "focus", "delay", "waitUntil", "switchPage",
    "variable", "if", "repeat", "stop", "iracingPit", "iracingChat",
}
CONDITION_TYPES = {"always", "processRunning", "windowFocused", "variable", "not", "and", "or"}
# Key names understood by SimDeck (simdeck_server/keys.py)
KEYS = (
    set("abcdefghijklmnopqrstuvwxyz0123456789")
    | {f"f{i}" for i in range(1, 25)} | {f"num{i}" for i in range(10)}
    | {"shift", "lshift", "rshift", "ctrl", "lctrl", "rctrl", "alt", "lalt", "ralt", "win", "rwin", "menu",
       "backspace", "tab", "enter", "pause", "capslock", "esc", "space", "pageup", "pagedown", "end", "home",
       "left", "up", "right", "down", "printscreen", "insert", "delete", "numlock", "scrolllock",
       "nummultiply", "numadd", "numsubtract", "numdecimal", "numdivide", "numenter", "semicolon", "equals",
       "comma", "minus", "period", "slash", "backquote", "bracketleft", "backslash", "bracketright", "quote",
       "intlbackslash", "volumemute", "volumedown", "volumeup", "medianext", "mediaprev", "mediastop",
       "mediaplaypause"}
)
KEY_ALIASES = {
    "control": "ctrl", "escape": "esc", "return": "enter", "del": "delete", "ins": "insert", "pgup": "pageup",
    "pgdn": "pagedown", "windows": "win", "cmd": "win", "altgr": "ralt", "arrowup": "up", "arrowdown": "down",
    "arrowleft": "left", "arrowright": "right",
}
IRACING_PIT_COMMANDS = {"clear", "windshield", "fuel", "lf", "rf", "lr", "rr", "clearTires", "fastRepair",
                        "clearWindshield", "clearFastRepair", "clearFuel", "tireCompound"}
IRACING_CHAT_MODES = {"macro", "begin", "reply", "cancel"}
INT_FIELDS = ("ms", "holdMs", "count", "delayMs", "timeoutMs", "pollMs", "macro")
STR_FIELDS = ("path", "args", "workingDir", "target", "command", "processName", "titleContains", "text",
              "skipIfRunning", "name", "pageId", "comment")
ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,40}")
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}")
MAX_GRID = 12
# Only these base plugins may be installed automatically on first start.
DEFAULT_ALLOWED = {"simracing", "flightsim", "windows"}
# Actions shown to the user as "what this plugin can do on the PC".
CAPABILITY_ACTIONS = {"launch", "open", "command", "kill", "text"}
# Button images: <plugin>/images/<preset id>.png (or @active for the active state)
IMAGE_RECOMMENDED = 128
IMAGE_MAX = 256
IMAGE_MAX_BYTES = 256 * 1024
IMAGE_FORMATS = {"png": ".png", "webp": ".webp"}
IMAGE_NAME_RE = re.compile(r"(?P<preset>[A-Za-z0-9_-]+)(?P<active>@active)?\.(?P<ext>png|webp)")


def norm_key(k: str) -> str:
    k = k.strip().lower().replace(" ", "")
    return KEY_ALIASES.get(k, k)


def version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


class Invalid(Exception):
    pass


def walk(actions, where):
    if not isinstance(actions, list):
        raise Invalid(f"{where} : liste d'actions attendue")
    for i, a in enumerate(actions):
        here = f"{where}[{i}]"
        if not isinstance(a, dict) or a.get("type") not in ACTION_TYPES:
            raise Invalid(f"{here} : type d'action inconnu {a.get('type') if isinstance(a, dict) else a!r}")
        yield a
        for field in INT_FIELDS:
            if field in a and (not isinstance(a[field], int) or isinstance(a[field], bool) or a[field] < 0):
                raise Invalid(f"{here} : « {field} » doit être un entier positif")
        for field in STR_FIELDS:
            if field in a and not isinstance(a[field], str):
                raise Invalid(f"{here} : « {field} » doit être un texte")
        if a["type"] == "hotkey":
            keys = a.get("keys")
            if not isinstance(keys, list) or not keys or not all(isinstance(k, str) for k in keys):
                raise Invalid(f"{here} : « keys » doit être une liste de touches")
            for k in keys:
                if norm_key(k) not in KEYS:
                    raise Invalid(f"{here} : touche inconnue « {k} »")
            if a.get("mode", "press") not in ("press", "down", "up"):
                raise Invalid(f"{here} : « mode » doit valoir press, down ou up")
        elif a["type"] == "iracingPit":
            if a.get("command") not in IRACING_PIT_COMMANDS:
                raise Invalid(f"{here} : commande de stand iRacing inconnue « {a.get('command')} »")
            if not isinstance(a.get("value", 0), (int, float)):
                raise Invalid(f"{here} : « value » doit être un nombre")
        elif a["type"] == "iracingChat" and a.get("mode", "macro") not in IRACING_CHAT_MODES:
            raise Invalid(f"{here} : mode de chat iRacing inconnu « {a.get('mode')} »")
        for cond_key in ("condition",):
            if cond_key in a:
                check_condition(a[cond_key], here)
        for nested in ("then", "else", "actions"):
            if nested in a:
                yield from walk(a[nested], f"{here}.{nested}")


def check_condition(c, where):
    if not isinstance(c, dict) or c.get("type") not in CONDITION_TYPES:
        raise Invalid(f"{where} : condition invalide")
    if "condition" in c:
        check_condition(c["condition"], where)
    for sub in c.get("conditions", []):
        check_condition(sub, where)


def load(path: Path, category: str) -> dict:
    try:
        p = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Invalid(f"JSON invalide : {exc}")
    if not isinstance(p, dict):
        raise Invalid("le plugin doit être un objet JSON")
    if p.get("id") != path.parent.name or not ID_RE.fullmatch(str(p.get("id", ""))):
        raise Invalid(f"« id » doit être égal au nom du dossier ({path.parent.name})")
    if p.get("category") != category:
        raise Invalid(f"« category » doit valoir « {category} » dans ce dossier")
    for key in ("name", "description", "icon", "author"):
        if not isinstance(p.get(key), str) or not p[key].strip():
            raise Invalid(f"« {key} » est obligatoire")
    if not VERSION_RE.fullmatch(str(p.get("version", ""))):
        raise Invalid("« version » doit être de la forme 1.2.3")
    if not VERSION_RE.fullmatch(str(p.get("minAppVersion", ""))):
        raise Invalid("« minAppVersion » doit être de la forme 1.2.3")
    if not COLOR_RE.fullmatch(str(p.get("color", ""))):
        raise Invalid("« color » doit être de la forme #RRGGBB")
    if p.get("default") and p["id"] not in DEFAULT_ALLOWED:
        raise Invalid("« default » est réservé aux plugins de base")
    auto = p.get("autoSwitch")
    if auto is not None and not (isinstance(auto, dict) and isinstance(auto.get("processName"), str)):
        raise Invalid("« autoSwitch » doit être un objet avec « processName »")
    for key in ("notes", "requires"):
        if not isinstance(p.get(key, []), list) or not all(isinstance(x, str) for x in p.get(key, [])):
            raise Invalid(f"« {key} » doit être une liste de textes")
    presets = p.get("presets")
    if not isinstance(presets, list) or not presets:
        raise Invalid("« presets » doit contenir au moins une touche")
    seen = set()
    for preset in presets:
        pid = preset.get("id") if isinstance(preset, dict) else None
        if not isinstance(pid, str) or pid in seen:
            raise Invalid(f"preset sans identifiant ou en double : {pid}")
        seen.add(pid)
        if not isinstance(preset.get("label"), str) or not preset["label"]:
            raise Invalid(f"{pid} : « label » obligatoire")
        check_style(preset, pid)
        if "activeStyle" in preset:
            if not isinstance(preset["activeStyle"], dict):
                raise Invalid(f"{pid} : « activeStyle » doit être un objet")
            check_style(preset["activeStyle"], f"{pid}.activeStyle")
        for key in ("actions", "longPressActions", "releaseActions"):
            list(walk(preset.get(key, []), f"{pid}.{key}"))
        if "activeWhen" in preset:
            check_condition(preset["activeWhen"], f"{pid}.activeWhen")
    boards = p.get("boards", [])
    if not isinstance(boards, list) or not all(isinstance(b, dict) for b in boards):
        raise Invalid("« boards » doit être une liste d'objets")
    for board in boards:
        bid = board.get("id")
        if not isinstance(board.get("buttons", []), list):
            raise Invalid(f"board {bid} : « buttons » doit être une liste")
        rows, cols = board.get("rows"), board.get("cols")
        if not isinstance(bid, str) or not isinstance(rows, int) or not isinstance(cols, int) \
                or not (1 <= rows <= MAX_GRID and 1 <= cols <= MAX_GRID):
            raise Invalid(f"board {bid} : identifiant ou dimensions invalides")
        cells = set()
        for b in board.get("buttons", []):
            if not isinstance(b, dict) or not isinstance(b.get("preset"), str) \
                    or not isinstance(b.get("row"), int) or not isinstance(b.get("col"), int):
                raise Invalid(f"board {bid} : touche invalide")
            if not (0 <= b["row"] < rows and 0 <= b["col"] < cols) or (b["row"], b["col"]) in cells:
                raise Invalid(f"board {bid} : touche hors grille ou case occupée deux fois")
            cells.add((b["row"], b["col"]))
    return p


def check_style(obj: dict, where: str) -> None:
    """Fields sent to the phone: wrong types would break the app's deck decoding."""
    for key in ("label", "icon", "image", "textColor", "description"):
        if key in obj and not isinstance(obj[key], str):
            raise Invalid(f"{where} : « {key} » doit être un texte")
    for key in ("color", "textColor"):
        if key in obj and not COLOR_RE.fullmatch(str(obj[key])):
            raise Invalid(f"{where} : « {key} » doit être de la forme #RRGGBB")
    if "fontSize" in obj and (isinstance(obj["fontSize"], bool) or not isinstance(obj["fontSize"], (int, float))):
        raise Invalid(f"{where} : « fontSize » doit être un nombre")
    if "showLabel" in obj and not isinstance(obj["showLabel"], bool):
        raise Invalid(f"{where} : « showLabel » doit valoir true ou false")


def capabilities(p: dict) -> list[str]:
    caps = set()
    for preset in p["presets"]:
        for key in ("actions", "longPressActions", "releaseActions"):
            for a in walk(preset.get(key, []), ""):
                if a["type"] in CAPABILITY_ACTIONS:
                    caps.add(a["type"])
    return sorted(caps)


def collect_images(p: dict, rel: str, errors: list[str], warnings: list[str]) -> list[dict]:
    folder = (ROOT / rel).parent / "images"
    if not folder.is_dir():
        return []
    presets = {x["id"] for x in p["presets"]}
    images, seen = [], set()
    for path in sorted(folder.iterdir()):
        irel = path.relative_to(ROOT).as_posix()
        m = IMAGE_NAME_RE.fullmatch(path.name)
        if not m or not path.is_file():
            errors.append(f"{irel} : nom invalide (attendu <id de touche>.png, .webp, ou <id>@active.png)")
            continue
        if m["preset"] not in presets:
            errors.append(f"{irel} : aucune touche « {m['preset']} » dans ce plugin")
            continue
        state = "active" if m["active"] else "default"
        if (m["preset"], state) in seen:
            errors.append(f"{irel} : deux images pour la même touche")
            continue
        seen.add((m["preset"], state))
        data = path.read_bytes()
        if len(data) > IMAGE_MAX_BYTES:
            errors.append(f"{irel} : fichier trop lourd ({len(data) // 1024} Ko, maximum {IMAGE_MAX_BYTES // 1024} Ko)")
            continue
        info = image_info(data)
        if not info or IMAGE_FORMATS.get(info[0]) != path.suffix:
            errors.append(f"{irel} : image PNG ou WebP invalide (ou extension ne correspondant pas au format)")
            continue
        _, w, h = info
        if w > IMAGE_MAX or h > IMAGE_MAX:
            errors.append(f"{irel} : {w}×{h} px, maximum autorisé {IMAGE_MAX}×{IMAGE_MAX}")
            continue
        if w < IMAGE_RECOMMENDED or h < IMAGE_RECOMMENDED:
            warnings.append(f"{irel} : {w}×{h} px, {IMAGE_RECOMMENDED}×{IMAGE_RECOMMENDED} conseillé pour une meilleure définition")
        images.append({"preset": m["preset"], "state": state, "path": irel,
                       "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
    return images


def build() -> tuple[dict, list[str], list[str]]:
    errors, warnings, plugins = [], [], {}
    for folder, category in FOLDERS.items():
        base = ROOT / folder
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*/plugin.json")):
            rel = path.relative_to(ROOT).as_posix()
            try:
                p = load(path, category)
            except Invalid as exc:
                errors.append(f"{rel} : {exc}")
                continue
            if p["id"] in plugins:
                errors.append(f"{rel} : identifiant déjà utilisé par {plugins[p['id']][1]}")
                continue
            plugins[p["id"]] = (p, rel)
    # Cross-plugin references
    for pid, (p, rel) in plugins.items():
        for req in p.get("requires", []):
            if req not in plugins:
                errors.append(f"{rel} : plugin requis introuvable « {req} »")
            elif plugins[req][0].get("requires"):
                # The app installs direct requirements only: no chains.
                errors.append(f"{rel} : « {req} » a lui-même des dépendances (une seule profondeur autorisée)")
        for board in p.get("boards", []):
            for b in board.get("buttons", []):
                owner, _, name = b["preset"].rpartition("/")
                owner = owner or pid
                if owner != pid and owner not in p.get("requires", []):
                    errors.append(f"{rel} : « {b['preset']} » utilise « {owner} » qui doit figurer dans « requires »")
                    continue
                target = plugins.get(owner)
                if not target or not any(x["id"] == name for x in target[0]["presets"]):
                    errors.append(f"{rel} : preset introuvable « {b['preset']} »")
    entries = []
    for pid, (p, rel) in sorted(plugins.items()):
        data = (ROOT / rel).read_bytes()
        entries.append({
            "id": pid,
            "name": p["name"],
            "version": p["version"],
            "minAppVersion": p["minAppVersion"],
            "category": p["category"],
            "icon": p["icon"],
            "color": p["color"],
            "author": p["author"],
            "description": p["description"],
            "default": bool(p.get("default")),
            "requires": p.get("requires", []),
            "presetCount": len(p["presets"]),
            "boardCount": len(p.get("boards", [])),
            "capabilities": capabilities(p),
            "path": rel,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "images": collect_images(p, rel, errors, warnings),
        })
    return {"schema": SCHEMA, "plugins": entries}, errors, warnings


def content_key(entry: dict) -> tuple:
    """Everything that users download for a plugin: its manifest and its images."""
    return entry["sha256"], tuple(sorted((i["path"], i["sha256"]) for i in entry.get("images", [])))


def main() -> int:
    index, errors, warnings = build()
    for w in warnings:
        print(f"AVERTISSEMENT {w}")
    for e in errors:
        print(f"ERREUR {e}")
    if errors:
        return 1
    text = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    if "--base" in sys.argv:
        base = json.loads(Path(sys.argv[sys.argv.index("--base") + 1]).read_text(encoding="utf-8"))
        old = {e["id"]: e for e in base.get("plugins", [])}
        bumps = [f"{e['path']} : contenu modifié, augmentez « version » (actuellement {e['version']})"
                 for e in index["plugins"]
                 if e["id"] in old and content_key(e) != content_key(old[e["id"]])
                 and version_tuple(e["version"]) <= version_tuple(old[e["id"]]["version"])]
        for b in bumps:
            print(f"ERREUR {b}")
        if bumps:
            return 1
    if "--check" in sys.argv:
        if not INDEX.exists() or INDEX.read_text(encoding="utf-8") != text:
            print("index.json n'est pas à jour : lancez `python tools/build_index.py` et commitez le résultat.")
            return 1
        print(f"OK : {len(index['plugins'])} plugins, index à jour")
        return 0
    INDEX.write_text(text, encoding="utf-8")
    print(f"index.json écrit : {len(index['plugins'])} plugins")
    return 0


if __name__ == "__main__":
    sys.exit(main())
