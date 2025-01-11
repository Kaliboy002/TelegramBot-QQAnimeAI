import logging
import base64
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.utils import executor
from aiohttp import ClientSession
from environs import Env

# Load environment variables
env = Env()
env.read_env()

TELEGRAM_TOKEN = env.str("TELEGRAM_TOKEN")
REPLICATE_API_TOKEN = env.str("REPLICATE_API_TOKEN")

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Configure logging
logging.basicConfig(level=logging.INFO)

REPLICATE_MODEL = "tencentarc/animeganv2"  # AnimeGANv2 model

async def replicate_anime_conversion(image_bytes: bytes) -> str:
    """
    Send the image to Replicate's AnimeGANv2 model for conversion.
    Returns the URL of the anime-styled image.
    """
    try:
        # Base64 encode the image
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        headers = {"Authorization": f"Token {REPLICATE_API_TOKEN}"}
        payload = {
            "version": "latest",  # Use the latest version of the model
            "input": {"image": f"data:image/jpeg;base64,{image_base64}"},
        }

        async with ClientSession() as session:
            async with session.post(
                f"https://api.replicate.com/v1/predictions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status == 201:
                    response_data = await response.json()
                    return response_data["urls"]["get"]  # URL to fetch the converted image
                else:
                    raise Exception(
                        f"Failed to send image to Replicate: {response.status}, {await response.text()}"
                    )
    except Exception as e:
        logging.error(f"Error in replicate_anime_conversion: {e}")
        raise


async def download_image(file_id: str) -> bytes:
    """
    Download an image from Telegram using its file ID.
    """
    try:
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        downloaded_file = await bot.download_file(file_path)
        return downloaded_file.read()
    except Exception as e:
        logging.error(f"Error in download_image: {e}")
        raise


async def upload_image_to_replicate(image_bytes: bytes) -> str:
    """
    Upload the image to Replicate's model and return the final anime image URL.
    """
    anime_image_url = await replicate_anime_conversion(image_bytes)
    return anime_image_url


@dp.message_handler(content_types=ContentType.PHOTO)
async def process_photo(message: types.Message):
    """
    Handles photo uploads, converts them to anime style, and sends them back.
    """
    await message.answer_chat_action("upload_photo")

    try:
        # Get the highest resolution photo
        photo = message.photo[-1]
        image_bytes = await download_image(photo.file_id)

        # Convert the image to anime style
        anime_image_url = await upload_image_to_replicate(image_bytes)

        # Send the anime-styled image URL back to the user
        await message.answer(f"Here is your anime-styled image:\n{anime_image_url}")

    except Exception as e:
        logging.exception("Error while processing photo")
        await message.answer("An error occurred while processing your photo. Please try again.")


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    """
    Handles /start and /help commands.
    """
    welcome_text = (
        "🎨 **Welcome to the Anime Style Converter Bot!**\n\n"
        "📷 Send me a photo, and I'll convert it into anime style using advanced AI.\n"
        "💡 Powered by Replicate's AnimeGANv2 model.\n\n"
        "**Commands:**\n"
        "/help - Show this help message\n"
    )
    await message.answer(welcome_text, parse_mode="Markdown")


if __name__ == "__main__":
    logging.info("Starting bot...")
    executor.start_polling(dp, skip_updates=True)
