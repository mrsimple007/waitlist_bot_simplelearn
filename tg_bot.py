import os
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from supabase import create_client, Client
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required environment variables SUPABASE_URL and SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

print("Using Telegram Bot Token:", BOT_TOKEN)

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

def get_tashkent_time():
    tashkent_tz = timezone(timedelta(hours=5))
    return datetime.now(tashkent_tz).isoformat()

START = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    current_time = get_tashkent_time()
    
    try:
        user_exists_tg = supabase.table('tgbot_waitlist').select("user_id").eq('user_id', str(user.id)).execute()
        
        if not user_exists_tg.data:
            tg_user_data = {
                'user_id': str(user.id),
                'first_name': user.first_name,
                'last_name': user.last_name if user.last_name else None,
                'username': user.username if user.username else None,
                'created_at': current_time
            }
            
            try:
                tg_user_data['last_interaction'] = current_time
                supabase.table('tgbot_waitlist').insert(tg_user_data).execute()
            except Exception:
                tg_user_data.pop('last_interaction', None)
                tg_user_data['last_interaction'] = current_time
                supabase.table('tgbot_waitlist').insert(tg_user_data).execute()
            
            logger.info(f"New user added to tgbot_waitlist: {user.id}")
        else:
            try:
                supabase.table('tgbot_waitlist').update({
                    'last_interaction': current_time
                }).eq('user_id', str(user.id)).execute()
            except Exception:
                supabase.table('tgbot_waitlist').update({
                    'last_interaction': current_time
                }).eq('user_id', str(user.id)).execute()
            
            logger.info(f"Updated last interaction for existing user in tgbot_waitlist: {user.id}")
        
        user_exists_sl = supabase.table('simplelearn_users').select("user_id").eq('user_id', str(user.id)).execute()
        
        if not user_exists_sl.data:
            simplelearn_user_data = {
                'user_id': str(user.id),
                'first_name': user.first_name,
                'last_name': user.last_name if user.last_name else None,
                'username': user.username if user.username else None,
                'created_at': current_time
            }
            
            try:
                simplelearn_user_data['last_interaction'] = current_time
                supabase.table('simplelearn_users').insert(simplelearn_user_data).execute()
            except Exception:
                simplelearn_user_data.pop('last_interaction', None)
                simplelearn_user_data['last_activity'] = current_time
                supabase.table('simplelearn_users').insert(simplelearn_user_data).execute()
            
            logger.info(f"New user added to simplelearn_users: {user.id}")
        else:
            try:
                supabase.table('simplelearn_users').update({
                    'last_interaction': current_time
                }).eq('user_id', str(user.id)).execute()
            except Exception:
                supabase.table('simplelearn_users').update({
                    'last_activity': current_time
                }).eq('user_id', str(user.id)).execute()
            
            logger.info(f"Updated last interaction for existing user in simplelearn_users: {user.id}")
    except Exception as e:
        logger.error(f"Error handling user data: {e}")

    welcome_message = (
        f"*Welcome to SimpleLearn! 🎓*\n\n"
        f"Hello *{user.first_name}*! 👋\n\n"
        f"*Thank you for joining our waitlist!* We're thrilled to have you as one of our early supporters.\n\n"
        f"🚀 We're currently developing an *AI-powered educational platform* that will revolutionize how you learn:\n"
        f"  • 📚 Smart document summarization\n"
        f"  • 📝 Exam preparation modules\n"
        f"  • 📅 Personalized study plans\n\n"
        f"⏱️ *Coming Soon in 2025!*\n\n"
        f"Join our channel: @SimpleLearnUz. We'll keep you updated on our progress and exciting new features. Type /help to discover more details about our upcoming project.\n\n"
        f"_Your journey to smarter learning starts here!_"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    user = update.effective_user
    current_time = get_tashkent_time()
    
    try:
        try:
            supabase.table('tgbot_waitlist').update({
                'last_interaction': current_time
            }).eq('user_id', str(user.id)).execute()
        except Exception:
            supabase.table('tgbot_waitlist').update({
                'last_interaction': current_time
            }).eq('user_id', str(user.id)).execute()
        
        try:
            supabase.table('simplelearn_users').update({
                'last_interaction': current_time
            }).eq('user_id', str(user.id)).execute()
        except Exception:
            supabase.table('simplelearn_users').update({
                'last_activity': current_time
            }).eq('user_id', str(user.id)).execute()
    except Exception as e:
        logger.error(f"Error updating interaction time: {e}")
    
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
    
    user = update.effective_user
    current_time = get_tashkent_time()
    
    try:
        try:
            supabase.table('tgbot_waitlist').update({
                'last_interaction': current_time
            }).eq('user_id', str(user.id)).execute()
        except Exception:
            supabase.table('tgbot_waitlist').update({
                'last_interaction': current_time
            }).eq('user_id', str(user.id)).execute()
        
        try:
            supabase.table('simplelearn_users').update({
                'last_interaction': current_time
            }).eq('user_id', str(user.id)).execute()
        except Exception:
            supabase.table('simplelearn_users').update({
                'last_activity': current_time
            }).eq('user_id', str(user.id)).execute()
    except Exception as e:
        logger.error(f"Error updating interaction time: {e}")
    
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
    try:
        result = supabase.table('tgbot_waitlist').select("*").limit(1).execute()
        print("✅ Supabase connection successful!")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    if test_supabase_connection():
        main()
    else:
        print("Bot not started due to database connection issues.")
