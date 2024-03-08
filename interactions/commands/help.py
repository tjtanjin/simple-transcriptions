import i18n

from telegram import Update
from telegram.ext import CallbackContext

from services.media_service import AUDIO_INPUT_TYPES
from services.media_service import IMAGE_INPUT_TYPES
from services.media_service import VIDEO_INPUT_TYPES
from services.message_service import reply


async def execute(update: Update, context: CallbackContext) -> None:
    """
    Lists all current transcription type information to user.
    Args:
        update: default telegram arg
        context: default telegram arg
    """
    await reply(update, help_message)


def build_help_message() -> str:
    """
    Builds the help message based on allowed input/output types.
    """
    message = i18n.t("help.header") + ":\n\n"

    # checks if image transcription is supported
    if image_transcription_supported():
        message += "<b>" + i18n.t("misc.images") + ":</b><pre>\n"
        message += build_types_body([i18n.t("misc.input") + ":"]) + "\n"
        message += build_types_body(
            list(map(lambda x: "." + x, IMAGE_INPUT_TYPES))
        )
        message += "</pre>\n"

    # checks if video transcription is supported
    if video_transcription_supported():
        message += "<b>" + i18n.t("misc.videos") + ":</b><pre>\n"
        message += build_types_body([i18n.t("misc.input") + ":"]) + "\n"
        message += build_types_body(
            list(map(lambda x: "." + x, VIDEO_INPUT_TYPES))
        )
        message += "</pre>\n"

    # checks if audio transcription is supported
    if audio_transcription_supported():
        message += "<b>" + i18n.t("misc.audio") + ":</b><pre>\n"
        message += build_types_body([i18n.t("misc.input") + ":"]) + "\n"
        message += build_types_body(
            list(map(lambda x: "." + x, AUDIO_INPUT_TYPES))
        )
        message += "</pre>\n"

    message += i18n.t("help.footer")
    return message


def build_types_body(input_array: list[str]) -> str:
    """
    Builds the body of the message that lists the allowed input types.
    Args:
        input_array: list of allowed inputs
    """
    parsed_input = list(map(pad_input, input_array))
    body = ""
    for i in range(0, len(parsed_input)):
        body += parsed_input[i] + "\n"

    return body


def pad_input(string: str) -> str:
    """
    Pads the allowed input type for formatting.
    Args:
        string: string to pad
    """
    string = "   " + string
    current_length = 0
    for char in string:
        if char.isascii():
            current_length += 1
        else:
            current_length += 2
    return string + ((12 - current_length) * " ")


def image_transcription_supported() -> bool:
    """
    Checks if image transcription is supported.
    """
    return len(IMAGE_INPUT_TYPES) > 0


def video_transcription_supported() -> bool:
    """
    Checks if video transcription is supported.
    """
    return len(VIDEO_INPUT_TYPES) > 0


def audio_transcription_supported() -> bool:
    """
    Checks if audio transcription is supported.
    """
    return len(AUDIO_INPUT_TYPES) > 0


help_message = build_help_message()
