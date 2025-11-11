#!/usr/bin/env zsh
## Script para desarrollo: activa virtualenv, instala deps opcionalmente, aplica migraciones y levanta runserver
# Uso: ./scripts/run_dev.sh [--install] [--host 0.0.0.0] [--port 8000]

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Prefer env/ (incluido en el repo) o .venv si existe
if [ -f "$ROOT_DIR/env/bin/activate" ]; then
  VENV="$ROOT_DIR/env"
elif [ -f "$ROOT_DIR/.venv/bin/activate" ]; then
  VENV="$ROOT_DIR/.venv"
else
  VENV=""
fi

INSTALL_DEPS=false
HOST=127.0.0.1
PORT=8000

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --install)
      INSTALL_DEPS=true; shift;;
    --host)
      HOST="$2"; shift 2;;
    --port)
      PORT="$2"; shift 2;;
    *)
      echo "Unknown option: $1"; exit 1;;
  esac
done

if [ -n "$VENV" ]; then
  echo "Activando virtualenv: $VENV"
  # shellcheck disable=SC1090
  source "$VENV/bin/activate"
else
  echo "No se encontró virtualenv local (env/ ni .venv). Se continuará con el Python del sistema/entorno actual." 
fi

if [ "$INSTALL_DEPS" = true ]; then
  if [ -f "$ROOT_DIR/req.txt" ]; then
    echo "Instalando dependencias desde req.txt..."
    pip install -r "$ROOT_DIR/req.txt"
  elif [ -f "$ROOT_DIR/requirements.txt" ]; then
    echo "Instalando dependencias desde requirements.txt..."
    pip install -r "$ROOT_DIR/requirements.txt"
  else
    echo "No se encontró archivo de requirements (req.txt o requirements.txt). Omisión de instalación." 
  fi
fi

echo "Aplicando migraciones..."
python "$ROOT_DIR/manage.py" migrate

echo "Iniciando servidor Django en ${HOST}:${PORT} (CTRL+C para parar)"
python "$ROOT_DIR/manage.py" runserver ${HOST}:${PORT}
