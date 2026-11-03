$env:UV_PROJECT_ENVIRONMENT = ".venv-windows"
$env:UV_LINK_MODE = "copy"
& uv @args
exit $LASTEXITCODE
