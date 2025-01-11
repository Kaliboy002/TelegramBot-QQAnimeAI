import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiohttp import ClientSession
from environs import Env
from qqddm import AnimeConverter, InvalidQQDDMApiResponseException, IllegalPictureQQDDMApiResponseException

# Load environment variables
env = Env()
env.read_env()

TELEGRAM_TOKEN = env.str("TELEGRAM_TOKEN")
PROXY = env.str("PROXY", None)

# Bot and Dispatcher setup
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Add logging
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())

# Anime converter instance
anime_converter = AnimeConverter(generate_proxy=PROXY)


async def download_image(file_id: str) -> bytes:
    """
    Download an image from Telegram using its file ID.
    """
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    downloaded_file = await bot.download_file(file_path)
    return downloaded_file.read()


async def upload_image(url: str) -> bytes:
    """
    Download the anime-converted image from the provided URL.
    """
    async with ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Failed to download anime image. HTTP Status: {response.status}")


@dp.message_handler(content_types=ContentType.PHOTO)
async def process_photo(message: types.Message):
    """
    Handles the photo upload, converts it to anime style, and sends it back to the user.
    """
    await message.answer_chat_action("upload_photo")

    try:
        # Get the highest resolution photo
        photo = message.photo[-1]
        image_bytes = await download_image(photo.file_id)

        # Convert to anime
        result = anime_converter.convert(picture=image_bytes)
        images = [str(url) for url in result.pictures_urls]

        # Download the converted image
        anime_image = await upload_image(images[0])

        # Send the anime-style photo to the user
        await message.answer_photo(anime_image, caption="Here is your anime-styled image!")

    except IllegalPictureQQDDMApiResponseException:
        await message.answer("The image is not valid for conversion. Please try another one.")
    except InvalidQQDDMApiResponseException as ex:
        await message.answer(f"API error: {ex}")
    except Exception as e:
        logging.exception("Error while processing photo")
        await message.answer("An unexpected error occurred. Please try again later.")


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    """
    Handles /start and /help commands.
    """
    welcome_text = (
        "Welcome to the Anime Style Converter Bot!\n"
        "Send me a photo, and I'll convert it into an anime style.\n\n"
        "Commands:\n"
        "/help - Show this help message\n"
    )
    await message.answer(welcome_text)


@dp.errors_handler(exception=Exception)
async def global_error_handler(update: types.Update, exception: Exception):
    """
    Global error handler for unexpected errors.
    """
    logging.exception(f"Update caused an error: {exception}")
    if isinstance(update, types.Message):
        await update.answer("An error occurred while processing your request.")
    return True


if __name__ == "__main__":
    logging.info("Starting bot...")
    executor.start_polling(dp, skip_updates=True)
