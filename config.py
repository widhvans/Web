import os

class Config:
    # Telegram Bot Token (Get from @BotFather)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8368477494:AAEVLeVK20P3xZUTSWbarOuqeTs_mgGitXE")
    
    # Groq API Key
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
    
    # Your Koyeb App URL
    WEBAPP_URL = "https://oral-melonie-as772685-9f0b873d.koyeb.app/"
    
    # Server Port (Koyeb uses 8000 by default)
    PORT = int(os.environ.get("PORT", 8080))

    GROQ_MODEL_NAME = "llama3-8b-8192"
