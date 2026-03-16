import os
import uvicorn
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from backend.db.models import init_db
from backend.api.telegram import init_telegram_app

app = FastAPI(title="Omnichannel AI Backend")

# Variable global para guardar la app de telegram
telegram_app = None

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    global telegram_app
    # 1. Creamos las tablas de la base de datos si no existen
    init_db()
    
    # 2. Inicializamos la App de Telegram
    telegram_app = await init_telegram_app()
    
    if telegram_app:
        # 3. Configuramos el Webhook
        webhook_url = os.getenv("WEBHOOK_URL") or os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if webhook_url:
            if not webhook_url.startswith("https://"):
                webhook_url = f"https://{webhook_url}"
            
            full_webhook_url = f"{webhook_url}/webhook"
            
            await telegram_app.bot.set_webhook(url=full_webhook_url)
            print(f"✅ Webhook registrado en: {full_webhook_url}")
            
            # Iniciamos la app (necesario aunque no usemos polling)
            await telegram_app.start()
        else:
            print("⚠️ WEBHOOK_URL no configurado. El bot no recibirá mensajes.")
    
    print("🚀 Sistema inicializado.")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Endpoint que recibe las actualizaciones de Telegram"""
    if telegram_app:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    return {"status": "ok"}

@app.get("/health")
def health_check():
    """Ruta para verificar que el servidor sigue vivo"""
    return {"status": "healthy", "service": "omnichannel_backend"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)