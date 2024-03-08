from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from services.message_service import update_message


def show_gemini_options() -> InlineKeyboardMarkup:
    """
    Generates Gemini option buttons for users from a list of button texts and callback data.
    """
    keyboard = [
        [InlineKeyboardButton("Summarize Content", callback_data='summary'),
         InlineKeyboardButton("Custom Instruction", callback_data='custom_instruction')],
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_animated_loader(message: str) -> None:
    """
    Provides loading animation during transcriptions.
    Args:
        message: message to edit to show loader
    """
    await update_message(message, text=message.text + " /", )
    await update_message(message, text=message.text + " -")
    await update_message(message, text=message.text + " \\")
    await update_message(message, text=message.text + " |")
