#!/usr/bin/env bash
# Idempotent setup for Red_Co-Author.
# Re-runnable: skips anything already in place.
#
# v1 needs: mistral (drafter), qwen3:8b (target).
# v2 adds:  llama3 (judge).
# v3/v4:    lmnr, streamlit, plotly — added in requirements.txt.
# v5 adds:  gemma2, phi3 (additional targets for the multi-model sweep).
# v7 adds:  nomic-embed-text (Ollama embeddings for the trained monitor).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

VENV_DIR=".venv"
REQUIRED_MODELS=("mistral" "qwen3:8b" "llama3" "gemma2" "phi3" "nomic-embed-text")

say()  { printf "\033[1;36m[setup]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m  %s\n" "$*"; }
die()  { printf "\033[1;31m[fail]\033[0m  %s\n" "$*" >&2; exit 1; }

# 1. Ollama binary
say "checking ollama..."
if ! command -v ollama >/dev/null 2>&1; then
  die "ollama is not installed. Install from https://ollama.com/download then re-run this script."
fi
say "ollama $(ollama --version 2>&1 | head -1)"

# 2. Ollama daemon
if ! ollama list >/dev/null 2>&1; then
  warn "ollama daemon not reachable. Start the Ollama app (macOS) or run 'ollama serve' in another terminal, then re-run."
  exit 1
fi

# 3. Models (idempotent — ollama pull is a no-op if already present)
installed_models="$(ollama list | awk 'NR>1 {print $1}')"
for model in "${REQUIRED_MODELS[@]}"; do
  if grep -qx "$model" <<<"$installed_models" || grep -qx "${model}:latest" <<<"$installed_models"; then
    say "model present: $model"
  else
    say "pulling $model ..."
    ollama pull "$model"
  fi
done

# 4. Python venv
if [ ! -d "$VENV_DIR" ]; then
  say "creating venv at $VENV_DIR ..."
  python3 -m venv "$VENV_DIR"
else
  say "venv present: $VENV_DIR"
fi

# 5. Python deps
say "installing python deps from requirements.txt ..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r requirements.txt

# 6. Smoke import
"$VENV_DIR/bin/python" -c "import ollama" || die "python 'ollama' import failed after install"

say "done. Activate with: source $VENV_DIR/bin/activate"
say "then run:           python run_pipeline.py"
