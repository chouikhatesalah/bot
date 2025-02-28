from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import yt_dlp
import os
import logging
import re
import tempfile
import time

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace 'YOUR_TOKEN' with the token you got from BotFather
TOKEN = '7739239357:AAGhs_xpLIQYk3ke-guXzayH395Daeg7XwY'

# Supported platforms for video download
SUPPORTED_PLATFORMS = ['instagram', 'tiktok', 'facebook', 'pinterest', 'twitter', 'youtube']

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    user_first_name = update.effective_user.first_name
    welcome_message = (
        f"👋 مرحبًا {user_first_name}!\n\n"
        "🎬 أرسل لي رابط فيديو من:\n"
        "• إنستغرام\n"
        "• تيك توك\n"
        "• فيسبوك\n"
        "• تويتر\n"
        "• يوتيوب\n"
        "• بنترست\n\n"
        "وسأقوم بتحميله وإرساله لك. 📲"
    )
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message when the command /help is issued."""
    help_text = (
        "💡 *كيفية استخدام البوت:*\n\n"
        "1️⃣ انسخ رابط الفيديو من التطبيق\n"
        "2️⃣ ألصق الرابط هنا وأرسله\n"
        "3️⃣ انتظر قليلاً حتى يتم معالجة الفيديو\n\n"
        "⚠️ *ملاحظات:*\n"
        "• قد لا تعمل بعض الروابط بسبب قيود المنصة\n"
        "• الفيديوهات الطويلة جدًا قد تستغرق وقتًا أطول\n"
        "• حجم الفيديو المرسل محدود بـ 50 ميغابايت\n\n"
        "🛠 *الأوامر المتاحة:*\n"
        "/start - بدء استخدام البوت\n"
        "/help - عرض رسالة المساعدة هذه\n"
        "/about - معلومات عن البوت"
    )
    update.message.reply_text(help_text, parse_mode='Markdown')

def about_command(update: Update, context: CallbackContext) -> None:
    """Send information about the bot when the command /about is issued."""
    about_text = (
        "ℹ️ *عن البوت*\n\n"
        "هذا البوت يساعدك في تحميل الفيديوهات من منصات التواصل الاجتماعي المختلفة.\n\n"
        "🔄 الإصدار: 1.0\n"
        "📅 آخر تحديث: فبراير 2025\n\n"
        "⚙️ مدعوم بواسطة:\n"
        "• python-telegram-bot\n"
        "• yt-dlp\n\n"
        "🔒 *خصوصية:* لا نقوم بتخزين الروابط أو الفيديوهات التي تقوم بتحميلها."
    )
    update.message.reply_text(about_text, parse_mode='Markdown')

def is_valid_url(url: str) -> bool:
    """Check if the message contains a valid URL for supported platforms."""
    url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)')
    
    if not url_pattern.match(url):
        return False
    
    # Check if URL is from a supported platform
    for platform in SUPPORTED_PLATFORMS:
        if platform in url.lower():
            return True
    
    return False

def download_video(url: str, update: Update, context: CallbackContext) -> None:
    """Download video from the provided URL and send it to the user."""
    status_message = update.message.reply_text("⏳ جاري معالجة الطلب... قد يستغرق هذا بضع ثوانٍ.")
    
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, 'video.mp4')
    
    try:
        # First try downloading with best quality
        ydl_opts = {
            'format': 'best',
            'outtmpl': temp_file,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')
            
            # Check if file exists and size
            if not os.path.exists(temp_file):
                # Try alternative file extension
                possible_extensions = ['.mp4', '.mkv', '.webm']
                for ext in possible_extensions:
                    alt_file = os.path.join(temp_dir, f'video{ext}')
                    if os.path.exists(alt_file):
                        temp_file = alt_file
                        break
            
            file_size = os.path.getsize(temp_file) / (1024 * 1024)  # Size in MB
            
            # If file exists and size is manageable for Telegram
            if os.path.exists(temp_file) and file_size < 50:
                # Update status message
                context.bot.edit_message_text(
                    chat_id=status_message.chat_id,
                    message_id=status_message.message_id,
                    text="✅ تم تحميل الفيديو! جاري الإرسال..."
                )
                
                # Send video with caption
                with open(temp_file, 'rb') as video_file:
                    update.message.reply_video(
                        video=video_file,
                        caption=f"📽️ {title}\n\n🔄 تم التحميل بواسطة @{context.bot.username}",
                        supports_streaming=True,
                        timeout=60
                    )
                
                # Delete status message
                context.bot.delete_message(
                    chat_id=status_message.chat_id,
                    message_id=status_message.message_id
                )
            else:
                # File too large, offer download options
                keyboard = [
                    [
                        InlineKeyboardButton("⬇️ تحميل بجودة منخفضة", callback_data=f"download_lower_{url}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                context.bot.edit_message_text(
                    chat_id=status_message.chat_id,
                    message_id=status_message.message_id,
                    text=f"⚠️ الفيديو كبير جدًا ({file_size:.1f} ميغابايت) للإرسال عبر تليجرام. الحد الأقصى هو 50 ميغابايت.\n\nهل تريد محاولة التحميل بجودة أقل؟",
                    reply_markup=reply_markup
                )
    
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        error_message = f"❌ عذرًا، حدث خطأ أثناء تحميل الفيديو:\n\n`{str(e)[:100]}`"
        
        # Check if it's a known error
        if "This video is unavailable" in str(e):
            error_message = "❌ هذا الفيديو غير متاح. قد يكون خاص أو تم حذفه."
        elif "Sign in" in str(e):
            error_message = "❌ هذا المحتوى يتطلب تسجيل الدخول ولا يمكن تحميله."
        elif "Requested format is not available" in str(e):
            error_message = "❌ الصيغة المطلوبة غير متاحة. حاول مع رابط آخر."
        
        # Update the status message with error info
        context.bot.edit_message_text(
            chat_id=status_message.chat_id,
            message_id=status_message.message_id,
            text=error_message,
            parse_mode='Markdown'
        )
    
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            os.rmdir(temp_dir)
        except:
            pass

def download_lower_quality(update: Update, context: CallbackContext) -> None:
    """Download video with lower quality when the button is pressed."""
    query = update.callback_query
    query.answer()
    
    # Extract URL from callback data
    _, _, url = query.data.partition('_lower_')
    
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, 'video_low.mp4')
    
    # Update message
    query.edit_message_text(text="⏳ جاري تحميل الفيديو بجودة منخفضة...")
    
    try:
        # Download with lower quality
        ydl_opts = {
            'format': 'worst[ext=mp4]',  # Lowest quality mp4
            'outtmpl': temp_file,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')
            
            # Check if file exists and size
            if os.path.exists(temp_file) and os.path.getsize(temp_file) / (1024 * 1024) < 50:
                # Send video with caption
                with open(temp_file, 'rb') as video_file:
                    context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=video_file,
                        caption=f"📽️ {title} (جودة منخفضة)\n\n🔄 تم التحميل بواسطة @{context.bot.username}",
                        supports_streaming=True,
                        timeout=60
                    )
                
                # Update message
                query.edit_message_text(text="✅ تم إرسال الفيديو بجودة منخفضة.")
            else:
                query.edit_message_text(text="❌ عذرًا، حتى الفيديو بجودة منخفضة كبير جدًا للإرسال عبر تليجرام.")
    
    except Exception as e:
        logger.error(f"Error downloading low quality video: {e}")
        query.edit_message_text(text=f"❌ حدث خطأ أثناء تحميل الفيديو بجودة منخفضة.")
    
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            os.rmdir(temp_dir)
        except:
            pass

def handle_message(update: Update, context: CallbackContext) -> None:
    """Process the user message and extract video if it contains a valid URL."""
    message_text = update.message.text
    
    # Check if message contains a valid URL
    if is_valid_url(message_text):
        download_video(message_text, update, context)
    else:
        update.message.reply_text(
            "❌ يرجى إرسال رابط صحيح من إحدى المنصات المدعومة:\n"
            "• إنستغرام\n"
            "• تيك توك\n"
            "• فيسبوك\n"
            "• تويتر\n"
            "• يوتيوب\n"
            "• بنترست"
        )

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Notify user of error
    if update.effective_message:
        update.effective_message.reply_text("⚠️ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى لاحقًا.")

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater(TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("about", about_command))
    
    # Add message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Add callback query handler for button
    dispatcher.add_handler(CallbackQueryHandler(download_lower_quality, pattern='^download_lower_'))
    
    # Add error handler
    dispatcher.add_error_handler(error_handler)
    
    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()