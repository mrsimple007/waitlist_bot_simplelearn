import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from supabase import create_client, Client
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import signal
import sys
import asyncio

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://enygxibkgjoqjmqsiwdi.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVueWd4aWJrZ2pvcWptcXNpd2RpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTMzOTkyOCwiZXhwIjoyMDYwOTE1OTI4fQ.YRUhwRt7SaAIejZebqxcRWism5Iuw79qS4dh4msjBFM")

supabase_url = SUPABASE_URL
supabase_key = SUPABASE_KEY
supabase: Client = create_client(supabase_url, supabase_key)

# Bot setup
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7782813133:AAHlfWIy_wDkug4KqjTN8yWtbBfWEiFYYko")

# HTTP Server setup
PORT = int(os.environ.get("PORT", 8080))

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "healthy"})
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Override to prevent logging every request
        pass

class HTTPServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        
    def run(self):
        try:
            logger.info(f"HTTP server running on port {PORT}")
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
        finally:
            self.server.server_close()

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()

START = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    user_data = {
        'user_id': str(user.id),
        'first_name': user.first_name,
        'last_name': user.last_name if user.last_name else None,
        'username': user.username if user.username else None,
        'join_date': datetime.now().isoformat()
    }
    
    # Save user to Supabase
    try:
        result = supabase.table('tgBot_waitlist').upsert(user_data).execute()
        logger.info(f"User data saved: {user.id}")
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

    welcome_message = (
        f"*Welcome to SimpleLearn! 🎓*\n\n"
        f"Hello *{user.first_name}*! 👋\n\n"
        f"*Thank you for joining our waitlist!* We're thrilled to have you as one of our early supporters.\n\n"
        f"🚀 We're currently developing an *AI-powered educational platform* that will revolutionize how you learn:\n"
        f"  • 📚 Smart document summarization\n"
        f"  • 📝 Exam preparation modules\n"
        f"  • 📅 Personalized study plans\n\n"
        f"⏱️ *Coming Soon in 2025!*\n\n"
        f"We'll keep you updated on our progress and exciting new features. Type /help to discover more details about our upcoming project.\n\n"
        f"_Your journey to smarter learning starts here!_"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send detailed information about the project when the command /help is issued."""
    help_message = (
        "🚀 *About Our Upcoming Project*\n\n"
        "🧠 *We are planning to add these Core Features*\n\n"
        "1️⃣ *📄 AI-Powered Summarization*\n"
        "Upload PDFs, YouTube links, podcasts, lecture notes, or text files. "
        "Our app extracts, transcribes, and summarizes content in Uzbek, Russian, or English.\n\n"
        
        "2️⃣ *🎯 Exam Preparation Modules*\n"
        "• Support for DTM (Uzbekistan) and IELTS exams\n"
        "• Subject-specific practice\n"
        "• Generate quizzes from your materials\n"
        "• Mini and Full Mock Exams with real conditions\n\n"
        
        "3️⃣ *📆 AI-Generated Study Plans*\n"
        "Get personalized weekly schedules based on your exam date and subjects.\n\n"
        
        "4️⃣ *🧪 Quiz Generation & Tracking*\n"
        "• Auto-generated quizzes from your materials\n"
        "• Multiple-choice questions\n"
        "• Timer-enabled quiz environment\n"
        "• Comprehensive progress tracking\n\n"
        
        "Stay tuned for more updates! We'll notify you when we're ready to launch."
    )
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and respond appropriately."""
    response = "Thanks for your message! If you need information about our project, please use the /help command."
    await update.message.reply_text(response)

async def main() -> None:
    """Start the bot and HTTP server."""
    # Start HTTP server in a separate thread
    http_server = HTTPServerThread()
    http_server.start()

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        http_server.shutdown()
        application.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Run the bot
    await application.initialize()
    await application.start()
    await application.run_polling()

def test_supabase_connection():
    """Test the Supabase connection and API key validity."""
    try:
        result = supabase.table('tgBot_waitlist').select("*").limit(1).execute()
        logger.info("✅ Supabase connection successful!")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        logger.error("\nPossible solutions:")
        logger.error("1. Check that your API key is correct")
        logger.error("2. Ensure you're using the 'service_role' key, not the 'anon' key")
        logger.error("3. Verify that the 'users' table exists in your database")
        logger.error("4. Check network connectivity to the Supabase server")
        return False

# Call this function before starting the bot
if __name__ == "__main__":
    if test_supabase_connection():
        asyncio.run(main())
    else:
        logger.error("Bot not started due to database connection issues.")
