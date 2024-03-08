import i18n
import os
import threading
from dataclasses import dataclass
from dataclasses import field

import google.generativeai as genai
from telegram.ext import CallbackContext

from services.message_service import send_message
from services.message_service import update_message
from services.cache_service import cache
from ui.builder import show_animated_loader

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')


@dataclass
class GeminiResult:
    """
    Temporary chat_id to gemini result cache to store and return gemini result to user.
    """
    results: dict = field(default_factory=dict)

    def get_result(self, chat_id: int) -> str:
        return self.results[chat_id]

    def set_result(self, chat_id: int, gemini_result: str) -> None:
        self.results[chat_id] = gemini_result

    def contains_result(self, chat_id: int) -> bool:
        return chat_id in self.results


gemini_result = GeminiResult()


def call_gemini_api(chat_id: int, message_id: int, instruction: str) -> None:
    """
    Makes a call to the Gemini API for results.
    Args:
        chat_id: id of user
        message_id: id of the transcript message
        instruction: instruction for the gemini ai
    """
    text = cache.get_transcript_content(chat_id, message_id)
    response = model.generate_content(f'{instruction}: "{text}"')
    gemini_result.set_result(chat_id, response.text)


async def get_gemini_result(context: CallbackContext, chat_id: int,
                            message_id: int, instruction: str = None) -> str:
    """
    Retrieves result from gemini api.
    Args:
        context: default telegram arg
        chat_id: id of user
        message_id: id of the transcript message
        instruction: instruction for the gemini ai
    """
    # if already have summary, just return from cache
    if instruction is None:
        if cache.contains_summary_content(chat_id, message_id):
            context.user_data[f"has_interaction_ongoing_{chat_id}"] = False
            return cache.get_summary_content(chat_id, message_id)
        else:
            instruction = os.getenv("SUMMARY_INSTRUCTION", "Provide a summary")

    try:
        # for all other cases we pass instruction and text to gemini api
        gemini_msg = await send_message(context, chat_id,
                                        i18n.t("interaction.retrieving_gemini_results"))
        gemini_in_progress_msg = i18n.t("gemini.in_progress")
        processing_msg = await update_message(gemini_msg, gemini_in_progress_msg)
        gemini_process = threading.Thread(target=call_gemini_api, args=(chat_id,
                                                                        message_id,
                                                                        instruction
                                                                        ))

        gemini_process.start()
        while gemini_process.is_alive():
            await show_animated_loader(processing_msg)

        await context.bot.delete_message(chat_id=chat_id, message_id=gemini_msg.message_id)

        if gemini_result.contains_result(chat_id):
            return gemini_result.get_result(chat_id)
        else:
            return i18n.t("misc.error")
    except Exception as e:
        print(e, flush=True)
        await update_message(gemini_msg, i18n.t("misc.error"))
    finally:
        context.user_data[f"has_interaction_ongoing_{chat_id}"] = False
