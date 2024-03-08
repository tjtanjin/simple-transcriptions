from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from interactions.utils import has_interaction_ongoing
from services.media_service import DOCUMENT_IMAGE_INPUT_TYPES
from services.media_service import DOCUMENT_VIDEO_INPUT_TYPES
from services.media_service import DOCUMENT_AUDIO_INPUT_TYPES
from services.media_service import process_media_upload
from services.message_service import end_conversation
from services.transcription_service import run_transcription_process


def handle_document_upload() -> MessageHandler:
    """
    Handles document input from user.
    """
    return MessageHandler(filters.Document.ALL, get_uploaded_document)


async def get_uploaded_document(update: Update, context: CallbackContext) -> int:
    """
    Captures uploaded documents that are media files and processes based on detected media type.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    chat_id = update.message.chat_id
    if await has_interaction_ongoing(update, context, chat_id, delete=True):
        return ConversationHandler.END

    file_id = update.message.document.file_id
    input_type = update.message.document.mime_type[6:]

    if input_type in DOCUMENT_VIDEO_INPUT_TYPES:
        receiving_msg = await process_media_upload(context, chat_id, file_id, "video", input_type)
        return await run_transcription_process(context, chat_id, receiving_msg, "video", input_type)
    elif input_type in DOCUMENT_IMAGE_INPUT_TYPES:
        receiving_msg = await process_media_upload(context, chat_id, file_id, "image", input_type)
        return await run_transcription_process(context, chat_id, receiving_msg, "image", input_type)
    elif input_type in DOCUMENT_AUDIO_INPUT_TYPES:
        receiving_msg = await process_media_upload(context, chat_id, file_id, "audio", input_type)
        return await run_transcription_process(context, chat_id, receiving_msg, "audio", input_type)
    else:
        return await end_conversation(context, chat_id, "interaction.file_not_supported")
