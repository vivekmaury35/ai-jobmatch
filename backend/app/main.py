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