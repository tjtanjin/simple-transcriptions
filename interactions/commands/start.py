import i18n

from telegram import Update
from telegram.ext import CallbackContext

from services.message_service import reply


async def execute(update: Update, context: CallbackContext) -> None:
    """
    Welcomes the user and prompts user to input files.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    await reply(update, i18n.t("start.message"))
