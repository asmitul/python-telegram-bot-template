import logging
import os
from dotenv import load_dotenv
load_dotenv()

LOGS_LOCATE = os.getenv("LOGS_LOCATE","LOCAL")

if LOGS_LOCATE == "LOCAL":
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")

    logging.basicConfig(
        filename=f"./app/logs/{current_date}.log",
        format="%(asctime)s %(levelname)s %(message)s",
        level=os.getenv("LOGGING_LEVEL")
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)

if LOGS_LOCATE == "REMOTE":
    from pymongo import MongoClient
    client = MongoClient(f'mongodb://{os.getenv("MONGODB_USER")}:{os.getenv("MONGODB_PASSWORD")}@{os.getenv("MONGODB_HOST")}:{os.getenv("MONGODB_PORT")}/?authMechanism=DEFAULT')
    db = client[os.getenv("APP_NAME")+os.getenv("MONGODB_LOGS_DATABASE_NAME")]
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    collection = db["log_"+current_date]

    logger = logging.getLogger(__name__)
    logger.setLevel(os.getenv("LOGGING_LEVEL"))

    class MongoDBhandler(logging.Handler):
        def emit(self, record):
            from datetime import datetime
            record.created = datetime.now().isoformat()
            collection.insert_one(record.__dict__)

    logger.addHandler(MongoDBhandler())

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler,filters,ContextTypes

TOKEN = os.getenv("TESTING_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!!")

    # for loop for testing 10 messages
    import time
    for i in range(5):
        time.sleep(0.5)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"this is message {i}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    application.add_handler(CommandHandler('start', start))    
    application.run_polling()