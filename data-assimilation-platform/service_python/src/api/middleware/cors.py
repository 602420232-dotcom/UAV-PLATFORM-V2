from fastapi.middleware.cors import CORSMiddleware
import os


def setup_cors(app):
    cors_str = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:8088,http://localhost:8080,http://localhost:5173",
    )
    cors_origins = cors_str.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin"],
    )
