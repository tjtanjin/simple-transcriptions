import json
import os
import re
import i18n

from telegram import Message
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from services.message_service import send_message
from services.message_service import update_message

# folders used
INPUT_MEDIA_FOLDER = os.getenv("INPUT_MEDIA_FOLDER", "input_media")
AUDIO_CHUNKS_FOLDER = os.getenv("AUDIO_CHUNKS_FOLDER", "audio_chunks")

# used to handle supported input media types
IMAGE_INPUT_TYPES = json.loads(os.getenv("IMAGE_INPUT_TYPES"))
VIDEO_INPUT_TYPES = json.loads(os.getenv("VIDEO_INPUT_TYPES"))
AUDIO_INPUT_TYPES = json.loads(os.getenv("AUDIO_INPUT_TYPES"))


# used to handle mime type checks on upload (fields auto-generated from supported types)
with open("./assets/file-extension-to-mime-types.json", "r") as file:
    mimetypes = json.load(file)
DOCUMENT_IMAGE_INPUT_TYPES = list(map(lambda input_type: mimetypes["image"][input_type],
                                      IMAGE_INPUT_TYPES))
DOCUMENT_VIDEO_INPUT_TYPES = list(map(lambda input_type: mimetypes["video"][input_type],
                                      VIDEO_INPUT_TYPES))
DOCUMENT_AUDIO_INPUT_TYPES = list(map(lambda input_type: mimetypes["audio"][input_type],
                                      AUDIO_INPUT_TYPES))


def create_media_folder(folder_path: str) -> None:
    """
    Creates folders if they do not exist.
    Args:
        folder_path: path to the folder to create
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created media folder: {folder_path}", flush=True)


create_media_folder(INPUT_MEDIA_FOLDER)
create_media_folder(AUDIO_CHUNKS_FOLDER)


def input_media_exist(chat_id: int, input_type: str) -> bool:
    """
    Checks if an input media uploaded by user exist.
    Args:
        chat_id: id of user
        input_type: format of media
    """
    if not os.path.isfile(f"./{INPUT_MEDIA_FOLDER}/{chat_id}.{input_type}"):
        return False
    directory, filename = os.path.split(f"./{INPUT_MEDIA_FOLDER}/{chat_id}.{input_type}")
    return filename in os.listdir(directory)


def clean_up_media(chat_id: int, input_type: str) -> None:
    """
    Cleans up input media files if it exist.
    Args:
        chat_id: use user id to identify media
        input_type: media input type
    """
    if input_media_exist(chat_id, input_type):
        os.remove(f"./{INPUT_MEDIA_FOLDER}/{chat_id}.{input_type}")


def purge_user_media(media_dir: str, chat_id: int) -> None:
    """
    Purges all media from a user in given directory.
    Used to handle cleanup during timeouts with untracked media types.
    Args:
        media_dir: directory where media is (input/output)
        chat_id: id of user to purge
    """
    for f in os.listdir(media_dir):
        if re.search(str(chat_id) + ".*", f):
            os.remove(os.path.join(media_dir, f))


async def process_media_upload(context: CallbackContext, chat_id: int, file_id: int,
                               media_category: str, input_type: str) -> Message:
    """
    Processes the media uploaded by user.
    Args:
        context: default telegram arg
        chat_id: id of user
        file_id: id of file uploaded
        media_cateogry: category of file uploaded (e.g. audio, video, image)
        input_type: type of file uploaded (e.g. jpg, mp3)
    """
    receiving_msg = await send_message(context, chat_id, i18n.t(f"{media_category}.detected"))
    try:
        new_file = await context.bot.get_file(file_id)
    except BadRequest:
        await update_message(receiving_msg, i18n.t("interaction.file_too_large"))
        return

    with open(f"./{INPUT_MEDIA_FOLDER}/{chat_id}.{input_type}", "wb") as file:
        await new_file.download_to_memory(file)
    return receiving_msg
