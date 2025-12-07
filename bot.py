import logging
import threading
import asyncio
from flask import Flask, render_template, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openai import OpenAI
from config import Config

# --- Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Flask Web App Setup ---
app = Flask(__name__)

# Initialize Groq Client
client = OpenAI(
    api_key=Config.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

@app.route('/')
def index():
    """Serves the HTML Chat Interface."""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check for Koyeb."""
    return "OK", 200

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handles the chat logic with Groq API."""
    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Call Groq API using the model from Config
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful, professional, and friendly AI assistant."
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            # USING THE MODEL FROM CONFIG
            model=Config.GROQ_MODEL_NAME, 
            temperature=0.7,
            max_tokens=1024,
        )
        
        bot_reply = chat_completion.choices[0].message.content
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Something went wrong with the AI."}), 500

# --- Telegram Bot Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the Start Chat button."""
    user_first_name = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("Start Chat 💬", url=Config.WEBAPP_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"Hello, {user_first_name}! 👋\n\n"
        "I am your AI Assistant powered by Groq.\n"
        "Click the button below to start a fast, intelligent conversation on our secure web interface."
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

def run_flask():
    """Runs the Flask server in a separate thread."""
    print(f"Starting Web Server on port {Config.PORT}...")
    # use_reloader=False is crucial when running in a thread
    app.run(host='0.0.0.0', port=Config.PORT, use_reloader=False)

def run_telegram_bot():
    """Runs the Telegram bot in the MAIN thread."""
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("Telegram Bot is polling...")
    application.run_polling()

# --- Main Execution ---
if __name__ == '__main__':
    # 1. Start Flask in a Background Thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True # Ensures thread dies when main program exits
    flask_thread.start()

    # 2. Start Telegram Bot in the Main Thread (Fixes the Signal Error)
    run_telegram_bot()
    
