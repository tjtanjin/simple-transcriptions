import aiohttp
import asyncio
import json
import os
import sys

if sys.platform.startswith('win') and sys.version_info[0] == 3 and sys.version_info[1] >= 8:
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)

API_ENDPOINT = os.getenv("API_ENDPOINT")
API_HEADERS = json.loads(os.getenv("API_HEADERS"))
API_BODY = json.loads(os.getenv("API_BODY"))


async def call_successful_transcription() -> None:
    """
    Makes an api call upon a successful transcription.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_ENDPOINT, headers=API_HEADERS, data=API_BODY):
                # no need to process response
                pass
    except (Exception,):
        # in the event of an exception, don't have to do anything (i.e. ok to lose some counts).
        pass
