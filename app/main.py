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
from telegram.constants import ParseMode 
import traceback
import html
import json

DEVELOPER_ID = os.getenv("DEVELOPER_ID")
TOKEN = os.getenv("TESTING_TOKEN")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # check message length , the limit is 4096
    if len(message) > 4096:
        message = message[:4096]
    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_ID, text=message, parse_mode=ParseMode.HTML
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!!")

    # for loop for testing 10 messages
    import time
    for i in range(5):
        time.sleep(0.5)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"this is message {i}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler('start', start))    
    application.run_polling()