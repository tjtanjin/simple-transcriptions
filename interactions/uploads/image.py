import i18n

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from services.transcription_service import run_transcription_process
from services.media_service import IMAGE_INPUT_TYPES
from services.media_service import process_media_upload
from services.message_service import end_conversation
from services.message_service import send_message
from interactions.utils import has_interaction_ongoing


def handle_image_upload() -> MessageHandler:
    """
    Handles image input from user.
    """
    return MessageHandler(filters.PHOTO, get_uploaded_image)


async def get_uploaded_image(update: Update, context: CallbackContext) -> int:
    """
    Captures uploaded images.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    chat_id = update.message.chat_id
    if await has_interaction_ongoing(update, context, chat_id, delete=True):
        return ConversationHandler.END

    file_id = update.message.photo[-1].file_id

    # images sent to telegram are by default received as jpg so a specific check is done here
    if "jpg" not in IMAGE_INPUT_TYPES:
        return await end_conversation(context, chat_id, "interaction.file_not_supported")

    # if sent as photo, no way to detect file name to parse type - hence defaults to jpg and users
    # are encouraged to send images as a file if transcription result is less than desirable
    await send_message(context, chat_id, i18n.t("image.advise"))

    receiving_msg = await process_media_upload(context, chat_id, file_id, "image", "jpg")
    return await run_transcription_process(context, chat_id, receiving_msg, "image", "jpg")
