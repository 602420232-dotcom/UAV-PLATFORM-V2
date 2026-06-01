from fastapi.middleware.cors import CORSMiddleware
import os


def setup_cors(app):
    cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:8088,http://localhost:8080").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False if cors_origins == ["*"] else True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
