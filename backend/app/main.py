from fastapi import FastAPI, Request, Response
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
# FAIL-SAFE CORS MIDDLEWARE
# ==========================================================

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        response = await call_next(request)

    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "X-Session-ID"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response


# ==========================================================
# SESSION MIDDLEWARE
# ==========================================================

@app.middleware("http")
async def session_middleware(
    request: Request,
    call_next,
):
    if request.method == "OPTIONS":
        return await call_next(request)

    session_id = request.cookies.get("session_id")
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    samesite_val = "none" if is_https else "lax"
    secure_val = is_https

    # No session cookie -> create one
    if not session_id:
        session_id = str(uuid4())

        response = await call_next(request)

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite=samesite_val,
            secure=secure_val,
        )

        return response

    # Validate existing session UUID
    try:
        UUID(session_id)

    except ValueError:
        session_id = str(uuid4())

        response = await call_next(request)

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite=samesite_val,
            secure=secure_val,
        )

        return response

    return await call_next(request)


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