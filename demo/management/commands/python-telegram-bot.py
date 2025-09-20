from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from demo.models import TGUsers

TOKEN = "7519143065:AAGYsojc-fz9dxY4S1VFQE3UvOxICoNK7ns"

@sync_to_async
def create_or_get_user(chat_id):
    return TGUsers.objects.get_or_create(chat_id=chat_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Бот может работать только в чатах или группах.")
        return

    chat_id = chat.id
    await create_or_get_user(chat_id)
    await update.message.reply_text("✅ Чат добавлен в список для уведомлений.")

class Command(BaseCommand):
    help = "Запуск telegram-бота"

    def handle(self, *args, **options):
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.run_polling()
