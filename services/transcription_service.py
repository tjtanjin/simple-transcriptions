import asyncio
import i18n
import speech_recognition as sr
import moviepy.editor as mp
import os
import threading
import pytesseract
from dataclasses import dataclass
from dataclasses import field

from PIL import Image
from pydub import AudioSegment
from pydub.silence import split_on_silence
from telegram import Message
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler

from services.api_service import call_successful_transcription
from services.cache_service import cache
from services.media_service import AUDIO_CHUNKS_FOLDER
from services.media_service import INPUT_MEDIA_FOLDER
from services.media_service import clean_up_media
from services.media_service import input_media_exist
from services.message_service import send_message
from services.message_service import send_transcript
from services.message_service import update_message
from ui.builder import show_animated_loader
from ui.builder import show_gemini_options

# check if api service is enabled
API_SERVICE_ENABLED = os.getenv("API_SERVICE_ENABLED")


@dataclass
class TranscriptResult:
    """
    Temporary chat_id to transcript result cache to store and return transcript result to user.
    """
    results: dict = field(default_factory=dict)

    def get_result(self, chat_id: int) -> str:
        return self.results[chat_id]

    def set_result(self, chat_id: int, transcript_result: str) -> None:
        self.results[chat_id] = transcript_result

    def contains_result(self, chat_id: int) -> bool:
        return chat_id in self.results


transcript_result = TranscriptResult()


# referenced from: https://thepythoncode.com/article/using-speech-recognition-to-convert-speech-to-text-python # noqa
# create a speech recognition object
r = sr.Recognizer()


def transcribe_audio(path: str) -> str:
    """
    Extracts speech from an audio chunk.
    Args:
        path: path to the audio chunk
    """
    # use the audio file as the audio source
    with sr.AudioFile(path) as source:
        audio_listened = r.record(source)
        # try converting it to text
        text = r.recognize_google(audio_listened)
    return text


def get_audio_transcription(chat_id: int, input_type: str) -> None:
    """
    Splits the large audio file into chunks and apply speech recognition on each of these chunks.
    Args:
        chat_id: id of user
        input_type: type of audio file
    """
    input_path = f"./{INPUT_MEDIA_FOLDER}/{chat_id}.{input_type}"
    # open the audio file using pydub
    sound = AudioSegment.from_file(input_path)
    # split audio sound where silence is 500 miliseconds or more and get chunks
    chunks = split_on_silence(sound, min_silence_len=500,
                              silence_thresh=sound.dBFS-14,
                              keep_silence=500)
    folder_name = f"{AUDIO_CHUNKS_FOLDER}/{chat_id}"
    # create a directory to store the audio chunks
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    whole_text = ""
    # process each chunk
    for i, audio_chunk in enumerate(chunks, start=1):
        # export audio chunk and save it in
        # the `folder_name` directory.
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")
        # recognize the chunk
        try:
            text = transcribe_audio(chunk_filename)
            whole_text += f"{text.capitalize()}. "
        except sr.UnknownValueError:
            pass
        finally:
            os.remove(chunk_filename)

    if whole_text.strip():
        transcript_result.set_result(chat_id, whole_text)

    if API_SERVICE_ENABLED:
        asyncio.run(call_successful_transcription())
    return None


def get_video_transcription(chat_id: int, input_type: str) -> None:
    """
    Loads a video and extract audio for transcription.
    Args:
        chat_id: id of user
        input_type: type of video file
    """
    # Load the video
    video_path = f"./{INPUT_MEDIA_FOLDER}/{chat_id}.{input_type}"
    video = mp.VideoFileClip(video_path)

    # Extract the audio from the video
    audio_file = video.audio
    audio_file.write_audiofile(f"./{INPUT_MEDIA_FOLDER}/{chat_id}.wav")

    return get_audio_transcription(chat_id, "wav")


def get_image_transcription(chat_id: int, input_type: str) -> None:
    """
    Uses pytesseract to extract text from image.
    Args:
        chat_id: id of user
        input_type: type of image file
    """
    input_path = f"./{INPUT_MEDIA_FOLDER}/{chat_id}.{input_type}"
    image = Image.open(input_path)
    text = pytesseract.image_to_string(image)

    if text is not None and text.strip():
        transcript_result.set_result(chat_id, text)

    if API_SERVICE_ENABLED:
        asyncio.run(call_successful_transcription())


async def run_transcription_process(context: CallbackContext, chat_id: int,
                                    receiving_msg: Message,
                                    media_category: str, input_type: str) -> int:
    """
    Runs the transcription process for the provided media file.
    Args:
        context: default telegram arg
        chat_id: id of user
        receiving_msg: message temporarily shown to user while transcripting
        media_category: category of file uploaded (e.g. audio, video, image)
        input_type: type of file uploaded (e.g. jpg, mp3)
    """
    if media_category == "audio":
        target = get_audio_transcription
    elif media_category == "video":
        target = get_video_transcription
    elif media_category == "image":
        target = get_image_transcription

    try:
        if not input_media_exist(chat_id, input_type):
            await send_message(context, chat_id, i18n.t("interaction.file_not_found"))
            return ConversationHandler.END

        transcription_in_progress_msg = i18n.t("transcription.in_progress", input_type=input_type)
        processing_msg = await update_message(receiving_msg, transcription_in_progress_msg)
        transcription_process = threading.Thread(target=target, args=(chat_id, input_type))
        transcription_process.start()
        while transcription_process.is_alive():
            await show_animated_loader(processing_msg)
        transcription_completed_msg = i18n.t("transcription.complete", input_type=input_type)
        await update_message(processing_msg, transcription_completed_msg)

        if transcript_result.contains_result(chat_id):
            transcript_content = transcript_result.get_result(chat_id)
            if transcript_content:
                message_id = await send_transcript(context, chat_id, transcript_content,
                                                   markup=show_gemini_options())
                cache.set_transcript_content(chat_id, message_id, transcript_content)
            else:
                await send_message(context, chat_id,
                                   i18n.t("transcription.no_text_found"))
        else:
            await send_message(context, chat_id,
                               i18n.t("transcription.no_text_found"))

    except Exception as e:
        print(e, flush=True)
        await update_message(receiving_msg, i18n.t("misc.error"))
    # remove all text output/files at the end
    finally:
        context.user_data[f"has_interaction_ongoing_{chat_id}"] = False
        clean_up_media(chat_id, input_type)
    return ConversationHandler.END
