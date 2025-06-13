import requests
import os
import json
import streamlit as st
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class APIClient:
    """
    Cliente para interactuar con la API del backend.
    """
    
    def __init__(self):
        """
        Inicializa el cliente API con la URL base desde las variables de entorno.
        """
        self.base_url = os.getenv("API_URL", "http://localhost:8000")
        
        # Asegurar que la URL base termina con /
        if not self.base_url.endswith("/"):
            self.base_url += "/"
        
        # Añadir prefijo de API si no está presente
        if not self.base_url.endswith("api/v1/"):
            self.base_url += "api/v1/"
    
    def _handle_response(self, response):
        """
        Maneja la respuesta de la API.
        
        Args:
            response: Objeto de respuesta de requests
        
        Returns:
            Datos de la respuesta o mensaje de error
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Intentar obtener detalles del error
            try:
                error_detail = response.json()
                return error_detail
            except:
                return {"detail": str(e)}
        except requests.exceptions.RequestException as e:
            return {"detail": str(e)}
        except json.JSONDecodeError:
            return {"detail": "Error al decodificar la respuesta JSON"}
    
    def get(self, endpoint, params=None):
        """
        Realiza una petición GET a la API.
        
        Args:
            endpoint: Ruta del endpoint
            params: Parámetros de la petición
        
        Returns:
            Datos de la respuesta
        """
        # Eliminar la barra inicial si está presente
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            return self._handle_response(response)
        except Exception as e:
            return {"detail": str(e)}
    
    def post(self, endpoint, json=None, data=None):
        """
        Realiza una petición POST a la API.
        
        Args:
            endpoint: Ruta del endpoint
            json: Datos JSON para enviar
            data: Datos form para enviar
        
        Returns:
            Datos de la respuesta
        """
        # Eliminar la barra inicial si está presente
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.post(url, json=json, data=data)
            return self._handle_response(response)
        except Exception as e:
            return {"detail": str(e)}
    
    def put(self, endpoint, json=None, data=None):
        """
        Realiza una petición PUT a la API.
        
        Args:
            endpoint: Ruta del endpoint
            json: Datos JSON para enviar
            data: Datos form para enviar
        
        Returns:
            Datos de la respuesta
        """
        # Eliminar la barra inicial si está presente
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.put(url, json=json, data=data)
            return self._handle_response(response)
        except Exception as e:
            return {"detail": str(e)}
    
    def delete(self, endpoint):
        """
        Realiza una petición DELETE a la API.
        
        Args:
            endpoint: Ruta del endpoint
        
        Returns:
            Datos de la respuesta
        """
        # Eliminar la barra inicial si está presente
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.delete(url)
            return self._handle_response(response)
        except Exception as e:
            return {"detail": str(e)}
