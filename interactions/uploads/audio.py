from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from interactions.utils import has_interaction_ongoing
from services.transcription_service import run_transcription_process
from services.media_service import DOCUMENT_AUDIO_INPUT_TYPES
from services.media_service import process_media_upload
from services.message_service import end_conversation


def handle_audio_upload() -> MessageHandler:
    """
    Handles audio input from user.
    """
    return MessageHandler(filters.AUDIO | filters.VOICE, get_uploaded_audio)


async def get_uploaded_audio(update: Update, context: CallbackContext) -> int:
    """
    Captures sent audio.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    chat_id = update.message.chat_id
    if await has_interaction_ongoing(update, context, chat_id, delete=True):
        return ConversationHandler.END

    # can be audio file or voice message
    if update.message.audio is None:
        file_id = update.message.voice.file_id
        input_type = update.message.voice.mime_type[6:]
    else:
        file_id = update.message.audio.file_id
        input_type = update.message.audio.mime_type[6:]

    if input_type not in DOCUMENT_AUDIO_INPUT_TYPES:
        return await end_conversation(context, chat_id, "interaction.file_not_supported")

    receiving_msg = await process_media_upload(context, chat_id, file_id, "audio", input_type)
    return await run_transcription_process(context, chat_id, receiving_msg, "audio", input_type)
