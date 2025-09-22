# app/main.py
"""
Main FastAPI application entrypoint.

Place this file at: app/main.py

This version:
- Registers available routers (auth, complaints, uploads, AI, storage/tests).
- Adds CORS middleware (adjust origins as needed).
- Provides a health-check root endpoint.
- Includes a simple startup/shutdown logger and an optional uvicorn block for local run.

Make sure the following router modules exist under app/routes/:
- auth_router.py        -> exposes `router`
- complaint_router.py   -> exposes `router`
- upload_router.py      -> exposes `router`
- ai_router.py          -> exposes `router`
- storage_test.py       -> exposes `router` (if present)
- test_db.py            -> exposes `router` (if present)

If any of them are not present, the code will skip registering that router but will log a warning.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from importlib import import_module
from typing import List, Tuple

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Civic Issue Backend",
    description="FastAPI backend for civic complaints (Auth + Complaints + Storage + AI)",
    version="1.0.0",
)

# CORS - adjust origins for your frontend hosts in production
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # add your deployed frontend origin(s) here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def root():
    """Health check / quick sanity endpoint"""
    return {"message": "Supabase Civic Backend up and running", "status": "ok"}


# Helper to try importing router modules safely
def try_register_router(module_path: str, prefix: str = None, tags: List[str] = None) -> Tuple[bool, str]:
    """
    Try to import module_path which should expose `router` and include it.
    Returns (success, message).
    """
    try:
        module = import_module(module_path)
    except Exception as e:
        msg = f"Could not import {module_path}: {e}"
        logger.warning(msg)
        return False, msg

    router = getattr(module, "router", None)
    if router is None:
        msg = f"Module {module_path} has no attribute 'router'."
        logger.warning(msg)
        return False, msg

    # include router with prefix/tags if provided
    kwargs = {}
    if prefix:
        kwargs["prefix"] = prefix
    if tags:
        kwargs["tags"] = tags

    app.include_router(router, **kwargs)
    msg = f"Registered router from {module_path} (prefix={prefix}, tags={tags})"
    logger.info(msg)
    return True, msg


# Attempt to register known routers. Adjust module paths if your project layout differs.
routers_to_register = [
    ("app.routes.auth_router", "/auth", ["Auth"]),
    ("app.routes.complaint_router", "/complaints", ["Complaints"]),
    ("app.routes.upload_router", "/files", ["Files"]),
    ("app.routes.ai_router", "/ai", ["AI"]),
    ("app.routes.storage_test", "/storage", ["Storage"]),
    ("app.routes.test_db", "/db", ["Database"]),
]

for module_path, prefix, tags in routers_to_register:
    ok, message = try_register_router(module_path, prefix=prefix, tags=tags)
    if not ok:
        logger.debug(f"Router registration skipped: {message}")


@app.on_event("startup")
async def on_startup():
    logger.info("Starting Civic Issue Backend application...")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down Civic Issue Backend application...")


# Local run helper: `python -m app.main` or `python app/main.py`
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
