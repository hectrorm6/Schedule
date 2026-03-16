import os
import google.generativeai as genai
from abc import ABC, abstractmethod
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class AIEngineInterface(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        pass

class GeminiEngine(AIEngineInterface):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ ERROR: Falta GEMINI_API_KEY en el .env")
            return
        
        genai.configure(api_key=api_key)
        # Usamos el modelo correcto
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_response(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        try:
            # Generamos la respuesta con el modelo 2.5
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text
            return "Recibí el mensaje, pero la respuesta está vacía."
        except Exception as e:
            print(f"❌ Error en Gemini 2.5: {e}")
            if "429" in str(e):
                return "⚠️ Límite de mensajes alcanzado (5 por minuto). Espera un momento."
            return f"Hubo un error con el modelo 2.5: {str(e)}"

class MockAIEngine(AIEngineInterface):
    async def generate_response(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        return f"MODO PRUEBA: {prompt}"

def get_ai_engine() -> AIEngineInterface:
    engine_type = os.getenv("AI_ENGINE_TYPE", "mock").lower()
    if engine_type == "gemini":
        return GeminiEngine()
    return MockAIEngine()