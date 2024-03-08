import i18n

from telegram import InlineKeyboardMarkup
from telegram import Message
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

MAX_MESSAGE_LENGTH = 4096


async def reply(update: Update, text: str,
                markup: InlineKeyboardMarkup = None,
                parse_mode: ParseMode = ParseMode.HTML) -> None:
    """
    Replies a user with the given message.
    Args:
        update: default telegram arg
        text: text message to reply to user with
        markup: markup for showing buttons, defaults to none
        parse_mode: mode to parse the string, defaults to HTML
    """
    await update.message.reply_text(text, reply_markup=markup, disable_web_page_preview=True,
                                    parse_mode=parse_mode)


async def send_message(context: CallbackContext, user_id: int, text: str,
                       markup: InlineKeyboardMarkup = None,
                       parse_mode: ParseMode = ParseMode.HTML) -> Message:
    """
    Sends a message to the user with the given id.
    Args:
        context: default telegram arg
        user_id: id of user to send message to
        text: text message to send user
        markup: markup for showing buttons, defaults to none
        parse_mode: mode to parse the string, defaults to HTML
    """
    return await context.bot.send_message(user_id, text, reply_markup=markup,
                                          disable_web_page_preview=True,
                                          parse_mode=parse_mode)


async def send_transcript(context: CallbackContext, user_id: int, text: str,
                          markup: InlineKeyboardMarkup = None,
                          parse_mode: ParseMode = ParseMode.MARKDOWN_V2) -> int:
    """
    Sends a transcript to the user with the given user id and returns id of the final sent message.
    Args:
        context: default telegram arg
        user_id: id of user to send message to
        text: text message to send user
        markup: markup for showing buttons, defaults to none
        parse_mode: mode to parse the string, defaults to markdown v2
    """
    text = escape_markdown(text, version=2)
    messages = [text[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]

    for index, msg in enumerate(messages):
        if index == len(messages) - 1:
            message = await send_message(context, user_id=user_id, text=msg,
                                         markup=markup, parse_mode=parse_mode)
        else:
            message = await send_message(context, user_id=user_id, text=msg, parse_mode=parse_mode)
    return message.message_id


async def update_message(message: Message, text: str,
                         markup: InlineKeyboardMarkup = None,
                         parse_mode: ParseMode = ParseMode.HTML) -> Message:
    """
    Updates an existing message with the user.
    Args:
        message: message to edit
        text: text to edit the message with
        markup: markup for showing buttons, defaults to none
        parse_mode: mode to parse the string, defaults to HTML
    """
    return await message.edit_text(text=text, reply_markup=markup, disable_web_page_preview=True,
                                   parse_mode=parse_mode)


async def end_conversation(context: CallbackContext, chat_id: int, message_key: str):
    """
    Ends a conversation with the user while performing cleanup logic.
    Args:
        context: default telegram arg
        chat_id: id of user
        message_key: key identifying i18n message to send
    """
    context.user_data[f"has_interaction_ongoing_{chat_id}"] = False
    await send_message(context, chat_id, i18n.t(message_key))
    return ConversationHandler.END
