from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from app.config import settings
from app.routes import articles, auth, market_data, technical_indicators, risk_appetite, company, fundamental_analysis
import uuid

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = str(uuid.uuid4())
    
    # Extract the first validation error for a cleaner message
    error_details = exc.errors()[0]
    
    # Try to get the cleaner error message from context first
    if "ctx" in error_details and "reason" in error_details["ctx"]:
        error_message = error_details["ctx"]["reason"]
    else:
        # Fallback to extracting the message after the colon
        full_message = error_details["msg"]
        if ": " in full_message:
            error_message = full_message.split(": ", 1)[1]
        else:
            error_message = full_message
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "data": {},
            "errorCode": 400003,
            "errorDesc": error_message,
            "requestId": request_id,
            "result": False
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = str(uuid.uuid4())
    
    # Map HTTP status codes to our error codes
    error_code_map = {
        400: 400001,
        401: 401001,
        403: 403001,
        404: 404001,
        422: 422001,
        500: 500001
    }
    
    error_code = error_code_map.get(exc.status_code, exc.status_code * 1000 + 1)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": {},
            "errorCode": error_code,
            "errorDesc": exc.detail,
            "requestId": request_id,
            "result": False
        }
    )

# Include routers
app.include_router(auth.router)
app.include_router(market_data.router)
app.include_router(fundamental_analysis.router)
app.include_router(technical_indicators.router)
app.include_router(articles.router)
app.include_router(risk_appetite.router)
app.include_router(company.router)

@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.VERSION
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)