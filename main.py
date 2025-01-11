import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your DeepAI API key and Telegram bot token
DEEP_AI_API_KEY = "ea3c67e9-af32-4eb1-b593-44b4ac8710f0"
TELEGRAM_BOT_TOKEN = "7628087790:AAFh_4CHHPVs2HKuOip9PROk7x3dfwG-A9w"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me an image, and I'll convert it to an anime style!")

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

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    file_path = "input.jpg"
    await photo_file.download_to_drive(file_path)

    await update.message.reply_text("Converting your image to anime style...")

    output_url = convert_to_anime(file_path)
    if output_url:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=output_url)
    else:
        await update.message.reply_text("Failed to convert the image. Please try again.")

    os.remove(file_path)  # Clean up

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    application.run_polling()

if __name__ == "__main__":
    main()
