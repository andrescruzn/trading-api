"""
Hook PreToolUse: bloquea la lectura y edición de .env, .env.production y .env.development.

Cubre las herramientas de archivos (Read, Edit, Write, MultiEdit, NotebookEdit, Grep, Glob)
y los comandos de shell (Bash, PowerShell) que mencionen esos archivos.
.env.example sigue permitido.
"""

import json
import re
import sys

# Nombres de archivo protegidos (basename exacto)
PROTECTED_NAME = re.compile(r"^\.env(\.production|\.development)?$", re.IGNORECASE)

# Mención de un archivo protegido dentro de un comando o patrón
PROTECTED_IN_TEXT = re.compile(
    r"(?:^|[\s/\\\"'=<>:(*])\.env(?:\.production|\.development)?(?![\w.-])",
    re.IGNORECASE,
)


def is_protected_path(path: str) -> bool:
    """True si la ruta apunta a un archivo .env protegido."""
    if not path:
        return False
    basename = re.split(r"[/\\]", path.rstrip("/\\"))[-1]
    return bool(PROTECTED_NAME.match(basename))


def touches_protected_env(text: str) -> bool:
    """True si el texto (comando, patrón) menciona un archivo .env protegido."""
    return bool(text) and bool(PROTECTED_IN_TEXT.search(text))


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def main() -> None:
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    blocked = False
    if tool in ("Read", "Edit", "Write", "MultiEdit"):
        blocked = is_protected_path(tool_input.get("file_path", ""))
    elif tool == "NotebookEdit":
        blocked = is_protected_path(tool_input.get("notebook_path", ""))
    elif tool == "Grep":
        # En Grep, "pattern" es el regex de contenido; lo que apunta a archivos es path y glob
        blocked = (
            is_protected_path(tool_input.get("path", ""))
            or touches_protected_env(tool_input.get("glob", ""))
        )
    elif tool == "Glob":
        blocked = touches_protected_env(tool_input.get("pattern", ""))
    elif tool in ("Bash", "PowerShell"):
        blocked = touches_protected_env(tool_input.get("command", ""))

    if blocked:
        _deny("Acceso bloqueado: .env, .env.production y .env.development contienen secretos. "
              "Usa .env.example como referencia.")


if __name__ == "__main__":
    main()
