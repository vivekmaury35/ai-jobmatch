from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from uuid import UUID, uuid4

from app.api.resumes import router as resumes_router
from app.api.jobs import router as jobs_router
from app.api.analyze import router as analyze_router


app = FastAPI(
    title="AI JobMatch API",
    description="Backend for AI JobMatch",
    version="1.0.0",
)


# ==========================================================
# GLOBAL EXCEPTION HANDLER (WITH CORS HEADERS FOR 500s)
# ==========================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_msg = f"{type(exc).__name__}: {str(exc)}"
    print(f"GLOBAL UNHANDLED EXCEPTION: {error_msg}\n{traceback.format_exc()}")

    origin = request.headers.get("origin") or "*"
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "INTERNAL_SERVER_ERROR", "message": error_msg}},
        headers=headers
    )


# ==========================================================
# STARTUP EVENT: AUTO-CREATE DATABASE TABLES
# ==========================================================

@app.on_event("startup")
def on_startup():
    try:
        import app.models
        from app.core.database import Base, engine
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        import logging
        logging.getLogger("uvicorn").error(f"Startup DB table creation error: {e}")


# ==========================================================
# DYNAMIC CORS MIDDLEWARE
# ==========================================================

@app.middleware("http")
async def dynamic_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin") or "*"

    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Session-ID, X-Requested-With, Accept",
                "Access-Control-Max-Age": "86400",
            }
        )

    response = await call_next(request)

    if origin != "*":
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Session-ID, X-Requested-With, Accept"
    response.headers["Access-Control-Expose-Headers"] = "X-Session-ID"

    return response


# ==========================================================
# SESSION MIDDLEWARE
# ==========================================================

@app.middleware("http")
async def session_middleware(
    request: Request,
    call_next,
):
    session_id = request.cookies.get("session_id") or request.headers.get("x-session-id")

    # No session ID -> create one
    if not session_id:
        session_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Session-ID"] = session_id
        return response

    # Validate existing session UUID
    try:
        UUID(session_id)
    except ValueError:
        session_id = str(uuid4())

    response = await call_next(request)
    response.headers["X-Session-ID"] = session_id
    return response


# ==========================================================
# API ROUTERS
# ==========================================================

app.include_router(
    resumes_router,
    prefix="/api",
)

app.include_router(
    jobs_router,
    prefix="/api",
)

app.include_router(
    analyze_router,
    prefix="/api",
)


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok"
    }