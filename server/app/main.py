from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    skus,
    ventas,
    produccion,
    pronostico,
    mps,
    kpis,
    parametros,
)
from app.db.session import create_db_and_tables
from app.core.config import settings

# Crear la aplicación FastAPI
app = FastAPI(
    title="Café de Altura API",
    description="API para el sistema de planificación de producción de Café de Altura",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(skus.router, prefix="/api/v1", tags=["SKUs"])
app.include_router(ventas.router, prefix="/api/v1", tags=["Ventas"])
app.include_router(produccion.router, prefix="/api/v1", tags=["Producción"])
app.include_router(pronostico.router, prefix="/api/v1", tags=["Pronóstico"])
app.include_router(mps.router, prefix="/api/v1", tags=["MPS"])
app.include_router(kpis.router, prefix="/api/v1", tags=["KPIs"])
app.include_router(parametros.router, prefix="/api/v1", tags=["Parámetros"])

# Endpoint de verificación de salud
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

# Endpoint de verificación de salud para la API
@app.get("/api/v1/health", tags=["Health"])
async def api_health_check():
    return {"status": "ok"}

# Manejador de excepciones global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error interno del servidor: {str(exc)}"},
    )

# Evento de inicio
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=True,
    )
