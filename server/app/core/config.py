from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings(BaseSettings):
    """
    Configuración de la aplicación.
    """

    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # Puerto del servidor
    PORT: int = int(os.getenv("PORT", "8000"))

    # Nivel de servicio para stock de seguridad (0-1)
    NIVEL_SERVICIO: float = float(os.getenv("NIVEL_SERVICIO", "0.95"))

    # Capacidad semanal en kg de café verde
    CAPACIDAD_SEMANAL: float = float(os.getenv("CAPACIDAD_SEMANAL", "300"))

    # Objetivos para KPIs
    DIAS_INVENTARIO_OBJETIVO: float = float(os.getenv("DIAS_INVENTARIO_OBJETIVO", "15"))
    OBJETIVO_CUMPLIMIENTO_PLAN: float = float(
        os.getenv("OBJETIVO_CUMPLIMIENTO_PLAN", "0.95")
    )
    OBJETIVO_OTD: float = float(os.getenv("OBJETIVO_OTD", "0.98"))
    OBJETIVO_RECHAZOS: float = float(os.getenv("OBJETIVO_RECHAZOS", "0.02"))

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia de configuración
settings = Settings()
