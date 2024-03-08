from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from services.transcription_service import run_transcription_process
from services.media_service import DOCUMENT_VIDEO_INPUT_TYPES
from services.media_service import process_media_upload
from services.message_service import end_conversation
from interactions.utils import has_interaction_ongoing


def handle_video_upload() -> MessageHandler:
    """
    Handles video input from user.
    """
    return MessageHandler(filters.VIDEO, get_uploaded_video)


async def get_uploaded_video(update: Update, context: CallbackContext) -> int:
    """
    Captures uploaded videos.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    chat_id = update.message.chat_id
    if await has_interaction_ongoing(update, context, chat_id, delete=True):
        return ConversationHandler.END

    file_id = update.message.video.file_id
    input_type = update.message.video.mime_type[6:]

    if input_type not in DOCUMENT_VIDEO_INPUT_TYPES:
        return await end_conversation(context, chat_id, "interaction.file_not_supported")

    receiving_msg = await process_media_upload(context, chat_id, file_id, "video", input_type)
    await run_transcription_process(context, chat_id, receiving_msg, "video", input_type)
