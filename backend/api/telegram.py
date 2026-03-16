import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
# Aquí usamos tu carpeta 'core'
from backend.core.ai_engine import get_ai_engine

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    print(f"📩 Telegram dice: {user_text}")

    # Llamamos a Gemini
    engine = get_ai_engine()
    response_text = await engine.generate_response(user_text)

    # Enviamos al móvil
    await update.message.reply_text(response_text)
    print("📤 IA respondió con éxito")

async def init_telegram_app():
    if not token or "860166" not in token:
        print("⚠️ Token de Telegram no detectado.")
        return None
    
    try:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_telegram_message))
        
        await app.initialize()
        return app
    except Exception as e:
        print(f"❌ Error al inicializar Telegram: {e}")
        return None