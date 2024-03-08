from telegram.ext import Application
from telegram.ext import CommandHandler

from interactions.commands.start import execute as start_e
from interactions.commands.help import execute as help_e
from interactions.gemini.gemini import handle_gemini_selection
from interactions.uploads.document import handle_document_upload
from interactions.uploads.audio import handle_audio_upload
from interactions.uploads.video import handle_video_upload
from interactions.uploads.image import handle_image_upload


def load_interactions(application: Application) -> None:
    """
    Loads all interactions on start.
    Args:
        application: application for adding handlers to
    """
    load_commands(application)
    load_gemini(application)
    load_uploads(application)


def load_commands(application: Application) -> None:
    """
    Loads all command handlers on start.
    Args:
        application: application for adding handlers to
    """
    application.add_handler(CommandHandler('start', start_e))
    application.add_handler(CommandHandler('help', help_e))


def load_gemini(application: Application) -> None:
    """
    Loads gemini handler on start.
    Args:
        application: application for adding handlers to
    """
    application.add_handler(handle_gemini_selection())


def load_uploads(application: Application) -> None:
    """
    Loads all handlers for media uploads on start.
    Args:
        application: application for adding handlers to
    """
    # handlers for media uploads
    application.add_handler(handle_document_upload())
    application.add_handler(handle_audio_upload())
    application.add_handler(handle_video_upload())
    application.add_handler(handle_image_upload())
