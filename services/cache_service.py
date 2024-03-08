from collections import OrderedDict
from dataclasses import dataclass
from dataclasses import field


@dataclass
class _TranscriptSummaryPair:
    """
    Model for containing a transcription content and its summary.
    """
    transcript_content: str
    summary_content: str | None = None


@dataclass
class Cache:
    """
    Cache is used to store transcript content and if applicable, its summary.
    """
    cache: OrderedDict = field(default_factory=OrderedDict)
    __limit: int = 50

    def set_transcript_content(self, chat_id: int, message_id: int,
                               transcript_content: str) -> None:
        """
        Sets the transcript content for given chat_id and message_id.
        Args:
            chat_id: id of user
            message_id: id of the transcript message
            transcript_content: contents of the transcript
        """
        self.cache[chat_id] = {message_id:
                               _TranscriptSummaryPair(transcript_content=transcript_content)}

        # ensure cache size stays within limit
        while len(self.cache) > self.__limit:
            self.cache.popitem(last=False)

    def valid_transcript_content(self, chat_id: int, message_id: int,
                                 transcript_content: str) -> bool:
        """
        Validates the transcript content for given chat_id and message_id.
        Args:
            chat_id: id of user
            message_id: id of the transcript message
            transcript_content: contents of the transcript
        """
        # if still has cache, then content is present
        if self.__contains_transcript_content(chat_id, message_id):
            return True
        # if it appears to fit within a single message, then just place the message in cache again
        elif len(transcript_content) < 4000:
            self.set_transcript_content(chat_id, message_id, transcript_content)
            return True
        # if above options fail, then no more valid transcript content
        return False

    def get_transcript_content(self, chat_id: int, message_id: int) -> str:
        """
        Retrieves the transcript content for given chat_id and message_id.
        Args:
            chat_id: id of user
            message_id: id of the transcript message
        """
        try:
            return self.cache[chat_id][message_id].transcript_content
        except KeyError:
            return None

    def __contains_transcript_content(self, chat_id: int, message_id: int) -> bool:
        """
        Checks for presence of the transcript content for given chat_id and message_id.
        Args:
            chat_id: id of user
            message_id: id of the transcript message
        """
        try:
            return self.cache[chat_id][message_id].transcript_content
        except KeyError:
            return False

    def set_summary_content(self, chat_id: int, message_id: int, summary_content: str) -> None:
        """
        Sets the summary content for given chat_id and message_id.
        Args:
            chat_id: id of user
            message_id: id of the transcript message that was summarized
            summary_content: contents of the summary
        """
        self.cache[chat_id][message_id].summary_content = summary_content

    def get_summary_content(self, chat_id: int, message_id: int) -> str:
        """
        Retrieves the summary content for given chat_id and message_id.
        Args:
            chat_id: id of user
            message_id: id of the transcript message that was summarized
        """
        try:
            return self.cache[chat_id][message_id].summary_content
        except KeyError:
            return None

    def contains_summary_content(self, chat_id: int, message_id: int) -> bool:
        """
        Checks for presence of the summary content for given chat_id and message_id.
        Args:
            chat_id: id of user
            message_id: id of the transcript message that was summarized
        """
        try:
            return self.cache[chat_id][message_id].summary_content
        except KeyError:
            return False


cache = Cache()
