import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from supabase import create_client, Client
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required environment variables SUPABASE_URL and SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing required environment variable TELEGRAM_BOT_TOKEN")

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

def run_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    logger.info(f"HTTP server running on port {PORT}")
    server.serve_forever()

START = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        tg_user_data = {
            'user_id': str(user.id),
            'first_name': user.first_name,
            'last_name': user.last_name if user.last_name else None,
            'username': user.username if user.username else None,
            'created_at': datetime.now().isoformat()
        }
        
        supabase.table('tgbot_waitlist').upsert(tg_user_data).execute()
        logger.info(f"User data saved to tgbot_waitlist: {user.id}")
        
        # Then insert into simplelearn_users
        simplelearn_user_data = {
            'user_id': str(user.id),
            'first_name': user.first_name,
            'last_name': user.last_name if user.last_name else None,
            'username': user.username if user.username else None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        supabase.table('simplelearn_users').upsert(simplelearn_user_data).execute()
        logger.info(f"User data saved to simplelearn_users: {user.id}")
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
        f"Join our channel: @SimpleLearnUz. We'll keep you updated on our progress and exciting new features. Type /help to discover more details about our upcoming project. \n\n"
        f"_Your journey to smarter learning starts here!_"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
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
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    response = "Thanks for your message! If you need information about our project, please use the /help command."
    await update.message.reply_text(response)

def main() -> None:
    http_thread = threading.Thread(target=run_http_server)
    http_thread.daemon = True
    http_thread.start()

    application = Application.builder().token(BOT_TOKEN).build()

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

    application.run_polling()

def test_supabase_connection():
    """Test the Supabase connection and API key validity."""
    try:
        result = supabase.table('tgbot_waitlist').select("*").limit(1).execute()
        print("✅ Supabase connection successful!")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        print("\nPossible solutions:")
        print("1. Check that your API key is correct")
        print("2. Ensure you're using the 'service_role' key, not the 'anon' key")
        print("3. Verify that the 'tgBot_waitlist' table exists in your database")
        print("4. Check network connectivity to the Supabase server")
        return False

if __name__ == "__main__":
    if test_supabase_connection():
        main()
    else:
        print("Bot not started due to database connection issues.")
