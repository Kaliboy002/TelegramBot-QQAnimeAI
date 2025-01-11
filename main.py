import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.utils import executor
from aiohttp import ClientSession
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Configure logging
logging.basicConfig(level=logging.INFO)


async def convert_to_anime(image_url: str) -> str:
    """
    Converts an image to anime style using DeepAI's API.
    """
    api_url = "https://api.deepai.org/api/toonify"
    headers = {"Api-Key": DEEPAI_API_KEY}
    data = {"image": image_url}

    async with ClientSession() as session:
        async with session.post(api_url, data=data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result["output_url"]
            else:
                logging.error(f"DeepAI API error: {response.status}")
                raise Exception("Failed to convert image to anime style.")


async def download_image(file_id: str) -> str:
    """
    Downloads the image from Telegram and uploads it to DeepAI's API.
    """
    file_info = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
    return file_url


@dp.message_handler(commands=["start", "help"])
async def welcome(message: types.Message):
    """
    Sends a welcome message with instructions.
    """
    welcome_text = (
        "🎨 **Welcome to the Anime Style Converter Bot!**\n\n"
        "📷 Send me a photo, and I'll convert it into anime style using DeepAI's API.\n"
        "💡 Powered by DeepAI's Toonify model.\n\n"
        "**Commands:**\n"
        "/help - Show this help message\n"
    )
    await message.reply(welcome_text, parse_mode="Markdown")


@dp.message_handler(content_types=ContentType.PHOTO)
async def handle_photo(message: types.Message):
    """
    Handles photo uploads and converts them to anime style.
    """
    await message.reply_chat_action("upload_photo")  # Show 'uploading' status in chat
    try:
        # Get the highest resolution photo
        photo = message.photo[-1]
        file_id = photo.file_id

        # Download image and get its URL
        image_url = await download_image(file_id)

        # Convert the image to anime style
        anime_image_url = await convert_to_anime(image_url)

        # Send the converted image back to the user
        await message.reply_photo(anime_image_url, caption="Here's your anime-styled image! 🎨")

    except Exception as e:
        logging.exception("Error while processing photo")
        await message.reply("❌ An error occurred while processing your photo. Please try again.")


if __name__ == "__main__":
    logging.info("Starting bot...")
    executor.start_polling(dp, skip_updates=True)
