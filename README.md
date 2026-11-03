# AI Customer Support

## Python environments

This project uses separate virtual environments because Windows and WSL cannot share an environment safely:

- `.venv-windows`: Native Windows environment used by VS Code and Jupyter Interactive.
- `.venv-linux`: Linux environment used from a WSL terminal.

Both environments are ignored by Git. Never run Jupyter kernels, Python, or `uv sync` in the environment belonging to the other platform.

### Windows and VS Code Jupyter

From PowerShell:

```powershell
.\scripts\uv-windows.ps1 sync
.\scripts\uv-windows.ps1 run python --version
```

VS Code should use:

```text
.venv-windows\Scripts\python.exe
```

When running Python scripts in the VS Code terminal or a notebook, use the Windows environment. In the Jupyter kernel picker, select **Python 3.13 (.venv-windows)**.

### WSL terminal

From a WSL terminal:

```bash
cd /mnt/c/w/ai/ai-customer-support
./scripts/uv-wsl.sh sync
./scripts/uv-wsl.sh run python --version
```

Commands executed with `scripts/uv-wsl.sh` always use `.venv-linux`, regardless of `.venv-windows`.

```bash
./scripts/uv-wsl.sh run fastapi dev app/main.py
./scripts/uv-wsl.sh run python -m app.poller
```

If the helper script is not executable, enable it once:

```bash
chmod +x scripts/uv-wsl.sh
```