import i18n
import os

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler

from services.media_service import purge_user_media
from services.message_service import send_message

try:
    TIMEOUT_DURATION = int(os.getenv("INTERACTION_TIMEOUT_DURATION"))
except ValueError:
    TIMEOUT_DURATION = 180


async def handle_interaction_timeout(update: Update, context: CallbackContext) -> int:
    """
    Handles logic for when a user interaction timeouts.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    chat_id = update.message.chat_id
    purge_user_media("./{INPUT_MEDIA_FOLDER}/", chat_id)
    return ConversationHandler.END


async def handle_interaction_not_allowed(update: Update, context: CallbackContext) -> None:
    """
    Handles logic for when a user performs an action not allowed during an interaction
    (e.g. uploading another file while there is an existing prompt).
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    chat_id = update.message.chat_id
    await context.bot.delete_message(chat_id, update.message.message_id)
    await send_message(context, chat_id, i18n.t("interaction.not_allowed"))


async def has_interaction_ongoing(update: Update, context: CallbackContext,
                                  chat_id: int, delete: bool = False) -> bool:
    """
    Handles logic for checking if a user has existing interaction ongoing.
    Args:
        update: default telegram arg
        context: default telegram arg
        chat_id: id of user
    """
    if context.user_data.get(f"has_interaction_ongoing_{chat_id}", False):
        if delete:
            await context.bot.delete_message(chat_id, update.message.message_id)
        await send_message(context, chat_id, i18n.t("interaction.not_allowed"))
        return True
    context.user_data[f"has_interaction_ongoing_{chat_id}"] = True
    return False
