
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
    """Serves the beautiful HTML Chat Interface."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handles the chat logic with Groq API."""
    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # call Groq API
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
            model="llama3-8b-8192", # Using Llama 3 on Groq for speed
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

def run_telegram_bot():
    """Runs the Telegram bot in a separate thread."""
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("Telegram Bot is polling...")
    # Use run_polling directly within the thread
    asyncio.set_event_loop(asyncio.new_event_loop())
    application.run_polling()

# --- Main Execution ---
if __name__ == '__main__':
    # Start Telegram Bot in a background thread so it doesn't block Flask
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.start()

    # Start Flask Server
    print(f"Starting Web Server on port {Config.PORT}...")
    app.run(host='0.0.0.0', port=Config.PORT)
  
