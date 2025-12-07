import logging
import threading
import asyncio
from flask import Flask, render_template, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openai import OpenAI
from config import Config

# --- 1. Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. Flask Web App Setup ---
app = Flask(__name__)

# Initialize Groq Client
# We use the keys from your config.py file
client = OpenAI(
    api_key=Config.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

@app.route('/')
def index():
    """Serves the beautiful HTML Chat Interface."""
    return render_template('index.html')

@app.route('/health')
def health():
    """
    Health check for Koyeb.
    Koyeb pings this to ensure the app is running.
    """
    return "OK", 200

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handles the chat logic with Groq API."""
    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Call Groq API
        # It uses the model defined in your config.py (openai/gpt-oss-120b)
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
            model=Config.GROQ_MODEL_NAME, 
            temperature=0.7,
            max_tokens=1024,
        )
        
        bot_reply = chat_completion.choices[0].message.content
        return jsonify({"reply": bot_reply})

    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        # If the model is decommissioned or key is wrong, this will print in logs
        return jsonify({"error": str(e)}), 500

# --- 3. Telegram Bot Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the Start Chat button."""
    user_first_name = update.effective_user.first_name
    
    # Create the button linking to your Web App
    keyboard = [
        [InlineKeyboardButton("Start Chat 💬", url=Config.WEBAPP_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"Hello, {user_first_name}! 👋\n\n"
        "I am your AI Assistant powered by Groq (120B Model).\n"
        "Click the button below to start a conversation."
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

def run_flask():
    """Runs the Flask server in a separate thread."""
    print(f"Starting Web Server on port {Config.PORT}...")
    # use_reloader=False is mandatory when running Flask in a thread
    app.run(host='0.0.0.0', port=Config.PORT, use_reloader=False)

def run_telegram_bot():
    """Runs the Telegram bot in the MAIN thread."""
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("Telegram Bot is polling...")
    # This blocks the main thread, which is what we want for signals to work
    application.run_polling()

# --- 4. Main Execution ---
if __name__ == '__main__':
    # A. Start Flask in a Background Thread
    # We set daemon=True so it shuts down when the main program stops
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True 
    flask_thread.start()

    # B. Start Telegram Bot in the Main Thread
    # This prevents the "set_wakeup_fd" error
    run_telegram_bot()
    
