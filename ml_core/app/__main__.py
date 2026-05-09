from __future__ import annotations

import uvicorn

from app.config import Settings


def main() -> None:
    settings = Settings.from_env()
    app_path = "app.inference_server:app"
    if settings.service_mode == "api":
        app_path = "app.server:app"
    elif settings.service_mode == "aligner":
        app_path = "app.aligner_server:app"
    elif settings.service_mode == "inference":
        app_path = "app.inference_server:app"
    uvicorn.run(app_path, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
