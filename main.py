import os
import requests
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace with your DeepAI API key and Telegram bot token
DEEP_AI_API_KEY = "ea3c67e9-af32-4eb1-b593-44b4ac8710f0"
TELEGRAM_BOT_TOKEN = "7628087790:AAFh_4CHHPVs2HKuOip9PROk7x3dfwG-A9w"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me an image, and I'll convert it to an anime style!")

def convert_to_anime(image_path: str) -> str:
    url = "https://api.deepai.org/api/toonify"
    with open(image_path, "rb") as image:
        response = requests.post(
            url,
            files={"image": image},
            headers={"api-key": DEEP_AI_API_KEY},
        )
    data = response.json()
    return data.get("output_url")

def handle_image(update: Update, context: CallbackContext):
    file = update.message.photo[-1].get_file()
    file_path = "input.jpg"
    file.download(file_path)

    update.message.reply_text("Converting your image to anime style...")

    output_url = convert_to_anime(file_path)
    if output_url:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=output_url)
    else:
        update.message.reply_text("Failed to convert the image. Please try again.")

    os.remove(file_path)  # Clean up

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
