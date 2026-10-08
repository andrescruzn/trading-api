"""
Hook PreToolUse: aprueba sin pedir permiso los comandos `uv` y `git`.

Solo aprueba comandos simples: si el comando encadena otros (;, &&, |, $(...), redirecciones…),
toca un archivo .env protegido o es una operación git destructiva, no decide nada y se aplica
el flujo de permisos normal.
"""

import json
import re
import sys

from protect_env_files import touches_protected_env

ALLOWED_PREFIX = re.compile(r"^(uv|git)(\s|$)")

# Metacaracteres que permiten encadenar o inyectar otros comandos (Bash y PowerShell)
SHELL_CHAINING = re.compile(r"[;&|`<>\n\r]|\$\(")

# Operaciones git que pierden trabajo o reescriben historia remota: se siguen preguntando
GIT_DESTRUCTIVE = re.compile(
    r"^git\s+("
    r"push\b.*(\s-f\b|--force)"
    r"|reset\b.*--hard"
    r"|clean\b.*\s-\w*f"
    r"|branch\b.*\s-D\b"
    r"|checkout\s+(--\s+)?\.\s*$"
    r"|restore\b"
    r"|stash\s+(drop|clear)\b"
    r")"
)


def main() -> None:
    data = json.load(sys.stdin)
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        return

    command = (data.get("tool_input", {}) or {}).get("command", "").strip()
    if not ALLOWED_PREFIX.match(command):
        return
    if SHELL_CHAINING.search(command) or touches_protected_env(command):
        return
    if GIT_DESTRUCTIVE.match(command):
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Comando uv/git aprobado automáticamente por hook del proyecto",
        }
    }))


if __name__ == "__main__":
    main()
