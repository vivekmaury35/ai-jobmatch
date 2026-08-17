from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID, uuid4

from app.api.resumes import router as resumes_router

app = FastAPI(
    title="AI JobMatch API",
    description="Backend for AI JobMatch",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session_id = request.cookies.get("session_id")

    if not session_id:
        session_id = str(uuid4())
        response = await call_next(request)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        return response

    try:
        UUID(session_id)
    except ValueError:
        session_id = str(uuid4())
        response = await call_next(request)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        return response

    return await call_next(request)


app.include_router(resumes_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}