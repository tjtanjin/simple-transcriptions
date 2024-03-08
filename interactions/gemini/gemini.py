import i18n

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from interactions.utils import TIMEOUT_DURATION
from interactions.utils import handle_interaction_not_allowed
from interactions.utils import handle_interaction_timeout
from interactions.utils import has_interaction_ongoing
from services.cache_service import cache
from services.gemini_service import GEMINI_API_KEY
from services.gemini_service import get_gemini_result
from services.message_service import send_message
from services.message_service import send_transcript


# maps prompt message id key from user to transcript message id
CUSTOM_INSTRUCTION_MESSAGE_ID_MAP = {}


def handle_gemini_selection() -> ConversationHandler:
    """
    Handles summary or custom instruction input from user.
    """
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_summary_selection, pattern='summary'),
                      CallbackQueryHandler(handle_custom_instruction_selection,
                                           pattern='custom_instruction')],
        states={
            1: [MessageHandler(filters.ALL, handle_custom_instruction_input)], # noqa
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, handle_interaction_timeout)]
        },
        fallbacks=[
            MessageHandler(filters.ALL & (~filters.COMMAND), handle_interaction_not_allowed)
        ],
        conversation_timeout=TIMEOUT_DURATION
    )


async def handle_summary_selection(update: Update,
                                   context: CallbackContext) -> int:
    """
    Summarizes the given text.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if not GEMINI_API_KEY:
        await send_message(context, chat_id, text=i18n.t("gemini.no_api_key"))
        return ConversationHandler.END

    if await has_interaction_ongoing(update, context, chat_id):
        return ConversationHandler.END

    message_id = query.message.message_id
    if not cache.valid_transcript_content(chat_id, message_id, query.message.text):
        return await end_conversation(context, chat_id, "transcription.invalid")
    summary = await get_gemini_result(context, chat_id, message_id)
    cache.set_summary_content(chat_id, message_id, summary)
    await send_transcript(context, chat_id, summary)
    return ConversationHandler.END


async def handle_custom_instruction_selection(update: Update,
                                              context: CallbackContext) -> int:
    """
    Prompts for customn instruction for given text.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if not GEMINI_API_KEY:
        await send_message(context, chat_id, text=i18n.t("gemini.no_api_key"))
        return ConversationHandler.END

    if await has_interaction_ongoing(update, context, chat_id):
        return ConversationHandler.END

    message_id = query.message.message_id
    if not cache.valid_transcript_content(chat_id, message_id, query.message.text):
        return await end_conversation(context, chat_id, "transcription.invalid")
    CUSTOM_INSTRUCTION_MESSAGE_ID_MAP[chat_id] = message_id
    await send_message(context, chat_id, i18n.t("interaction.prompt_provide_custom_instruction"))
    return 1


async def handle_custom_instruction_input(update: Update,
                                          context: CallbackContext) -> int:
    """
    Handles customn instruction for given text.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    chat_id = update.message.chat.id
    if chat_id not in CUSTOM_INSTRUCTION_MESSAGE_ID_MAP:
        await send_message(context, chat_id, text=i18n.t("transcription.invalid"))
        return ConversationHandler.END
    result = await get_gemini_result(context, chat_id,
                                     CUSTOM_INSTRUCTION_MESSAGE_ID_MAP[chat_id],
                                     update.message.text)
    await send_transcript(context, chat_id, result)
    return ConversationHandler.END
