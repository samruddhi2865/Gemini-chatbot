"""
Chatbot brain: talks to Gemini, remembers the conversation,
manages context, retries temporary Gemini errors, and uses
fallback models when necessary.
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)

FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-3.6-flash,gemini-3.1-flash-lite"
    ).split(",")
    if m.strip()
]

# Remove duplicates while preserving order
MODELS = []

for model in [MODEL] + FALLBACK_MODELS:
    if model and model not in MODELS:
        MODELS.append(model)


THINKING_LEVEL = os.getenv(
    "GEMINI_THINKING_LEVEL",
    "minimal"
)


# ============================================================
# CHAT SETTINGS
# ============================================================

# Maximum number of messages stored before context management
MAX_MESSAGES = 10

# Number of recent messages to keep
KEEP_RECENT = 6

# Maximum characters allowed in one user message
MAX_INPUT_CHARS = 2000

# Gemini timeout
# Increased from 15 seconds to 60 seconds
TIMEOUT_MS = 60_000

# Number of retries for temporary errors
MAX_RETRIES = 2

# Seconds to wait before retrying
RETRY_DELAY = 3


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are Pixel, a friendly coding mentor for beginner programmers.

Rules:

- Explain things in simple, easy language.
- Use short examples when useful.
- Keep answers under 150 words unless the user asks for more detail.
- If the user asks something unrelated to programming or tech learning,
  politely steer the chat back to those topics.
- Remember what the user told you earlier in the chat
  such as name, goals, and programming level.
- Use previous conversation context naturally.
- Never invent facts.
- If you are not sure, say so.
"""


# ============================================================
# CUSTOM ERROR
# ============================================================

class ChatbotError(Exception):
    """
    Error with a friendly message that can safely
    be shown to the frontend.
    """

    def __init__(self, message, status=500):
        super().__init__(message)
        self.message = message
        self.status = status


# ============================================================
# GEMINI CLIENT
# ============================================================

if API_KEY:

    client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(
            timeout=TIMEOUT_MS
        )
    )

else:

    client = None


# ============================================================
# CONVERSATION STORAGE
# ============================================================

# conversation_id -> {
#     "history": [
#         {"role": "user", "text": "..."},
#         {"role": "model", "text": "..."}
#     ],
#     "summary": "..."
# }

conversations = {}


# ============================================================
# GET / CREATE CONVERSATION
# ============================================================

def _get_conversation(cid):

    return conversations.setdefault(
        cid,
        {
            "history": [],
            "summary": ""
        }
    )


# ============================================================
# CONVERT HISTORY TO GEMINI FORMAT
# ============================================================

def _to_contents(history):

    return [
        types.Content(
            role=message["role"],
            parts=[
                types.Part(
                    text=message["text"]
                )
            ]
        )
        for message in history
    ]


# ============================================================
# CALL GEMINI
# ============================================================

def _call_model(contents, system_instruction):

    """
    Call Gemini.

    Handles:
        503 UNAVAILABLE
        504 DEADLINE_EXCEEDED
        429 RATE LIMIT

    It retries temporary errors and then moves
    to the next fallback model.
    """

    if client is None:

        raise ChatbotError(
            "Server is missing GEMINI_API_KEY. "
            "Check your .env file.",
            500
        )


    last_error = None


    # --------------------------------------------------------
    # Try every model
    # --------------------------------------------------------

    for model in MODELS:

        print()
        print("=" * 60)
        print(f"[Gemini] Trying model: {model}")
        print("=" * 60)


        # ----------------------------------------------------
        # Retry the same model
        # ----------------------------------------------------

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                print(
                    f"[Gemini] Attempt "
                    f"{attempt}/{MAX_RETRIES}"
                )


                response = client.models.generate_content(

                    model=model,

                    contents=contents,

                    config=types.GenerateContentConfig(

                        system_instruction=system_instruction,

                        thinking_config=types.ThinkingConfig(
                            thinking_level=THINKING_LEVEL
                        )
                    )
                )


                # ------------------------------------------------
                # Check response
                # ------------------------------------------------

                if not response.text:

                    raise ChatbotError(
                        "Gemini returned an empty response. "
                        "Please try asking your question again.",
                        502
                    )


                print(
                    f"[Gemini] SUCCESS using {model}"
                )

                print("=" * 60)
                print()


                return response.text


            # ----------------------------------------------------
            # Our own chatbot errors
            # ----------------------------------------------------

            except ChatbotError:

                raise


            # ----------------------------------------------------
            # Gemini API errors
            # ----------------------------------------------------

            except errors.APIError as e:

                code = getattr(e, "code", None)

                print()
                print(
                    f"[Gemini API error]"
                )

                print(
                    f"Model: {model}"
                )

                print(
                    f"Attempt: {attempt}/{MAX_RETRIES}"
                )

                print(
                    f"Code: {code}"
                )

                print(
                    f"Error: {e}"
                )


                # ------------------------------------------------
                # Invalid API key
                # ------------------------------------------------

                if code in (401, 403):

                    raise ChatbotError(

                        "Gemini API key was rejected. "
                        "Please create a new API key and update "
                        "your .env file.",

                        500
                    )


                last_error = code


                # ------------------------------------------------
                # Temporary errors
                # ------------------------------------------------

                if code in (429, 503, 504):

                    if attempt < MAX_RETRIES:

                        print(
                            f"[Gemini] Temporary error {code}. "
                            f"Waiting {RETRY_DELAY} seconds..."
                        )

                        time.sleep(RETRY_DELAY)

                        continue


                    print(
                        f"[Gemini] {model} failed after "
                        f"{MAX_RETRIES} attempts."
                    )

                    break


                # ------------------------------------------------
                # Unknown model
                # ------------------------------------------------

                if code == 404:

                    print(
                        f"[Gemini] Model {model} "
                        f"is not available."
                    )

                    break


                # ------------------------------------------------
                # Other API error
                # ------------------------------------------------

                print(
                    "[Gemini] Unexpected API error. "
                    "Trying next model."
                )

                break


            # ----------------------------------------------------
            # Network / timeout / other errors
            # ----------------------------------------------------

            except Exception as e:

                print()
                print(
                    "[Network/other error]"
                )

                print(
                    f"Model: {model}"
                )

                print(
                    f"Attempt: {attempt}/{MAX_RETRIES}"
                )

                print(
                    f"Type: {type(e).__name__}"
                )

                print(
                    f"Error: {e}"
                )


                last_error = "network"


                if attempt < MAX_RETRIES:

                    print(
                        f"[Gemini] Waiting "
                        f"{RETRY_DELAY} seconds before retry..."
                    )

                    time.sleep(RETRY_DELAY)

                    continue


                break


        # --------------------------------------------------------
        # Move to next fallback model
        # --------------------------------------------------------

        print(
            f"[Gemini] Moving to next model..."
        )


    # ============================================================
    # ALL MODELS FAILED
    # ============================================================

    print()
    print("=" * 60)
    print("[Gemini] ALL MODELS FAILED")
    print("=" * 60)
    print()


    if last_error == 429:

        raise ChatbotError(

            "Gemini rate limit reached. "
            "Please wait a little and try again.",

            429
        )


    if last_error == "network":

        raise ChatbotError(

            "Could not connect to Gemini. "
            "Please check your internet connection "
            "and try again.",

            504
        )


    if last_error == 504:

        raise ChatbotError(

            "Gemini took too long to respond. "
            "Please try again in a few seconds.",

            504
        )


    if last_error == 503:

        raise ChatbotError(

            "Gemini is temporarily busy. "
            "Please wait a few seconds and try again.",

            503
        )


    raise ChatbotError(

        "Gemini is currently unavailable. "
        "Please try again shortly.",

        503
    )


# ============================================================
# SUMMARIZE OLD CONVERSATION
# ============================================================

def _summarise(old_summary, old_messages):

    """
    Convert older messages into a short summary
    so the conversation does not become too large.
    """

    transcript = "\n".join(

        f"{'User' if m['role'] == 'user' else 'Bot'}: "
        f"{m['text']}"

        for m in old_messages
    )


    prompt = (

        f"Existing summary:\n"
        f"{old_summary or '(none)'}\n\n"

        f"New messages:\n"
        f"{transcript}\n\n"

        "Write an updated summary in under 120 words. "
        "Keep names, facts, goals, preferences and "
        "unanswered questions."
    )


    contents = [

        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=prompt
                )
            ]
        )

    ]


    return _call_model(

        contents,

        "You write short, accurate conversation summaries."
    )


# ============================================================
# MANAGE CONVERSATION CONTEXT
# ============================================================

def _manage_context(conv):

    """
    Keep conversation history small.
    """

    history = conv["history"]


    # Nothing to do yet
    if len(history) <= MAX_MESSAGES:

        return


    # Separate old and recent messages
    old = history[:-KEEP_RECENT]

    recent = history[-KEEP_RECENT:]


    try:

        conv["summary"] = _summarise(
            conv["summary"],
            old
        )

    except ChatbotError:

        # If summarization fails,
        # keep the chat working using simple truncation.
        print(
            "[Context] Summary failed. "
            "Using recent messages only."
        )


    conv["history"] = recent


# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def chat(conversation_id, user_message):

    """
    Process one user message.
    """

    # --------------------------------------------------------
    # Validate message
    # --------------------------------------------------------

    user_message = (
        user_message or ""
    ).strip()


    if not user_message:

        raise ChatbotError(
            "Please type a message first.",
            400
        )


    if len(user_message) > MAX_INPUT_CHARS:

        raise ChatbotError(

            f"Message too long. "
            f"Maximum allowed length is "
            f"{MAX_INPUT_CHARS} characters.",

            400
        )


    # --------------------------------------------------------
    # Get conversation
    # --------------------------------------------------------

    conv = _get_conversation(
        conversation_id
    )


    # --------------------------------------------------------
    # Manage old context
    # --------------------------------------------------------

    _manage_context(conv)


    # --------------------------------------------------------
    # Build system prompt
    # --------------------------------------------------------

    system = SYSTEM_PROMPT


    if conv["summary"]:

        system += (

            "\n\nSummary of the earlier conversation:\n"
            + conv["summary"]
        )


    # --------------------------------------------------------
    # Add current user message
    # --------------------------------------------------------

    new_message = {

        "role": "user",

        "text": user_message
    }


    # --------------------------------------------------------
    # Send to Gemini
    # --------------------------------------------------------

    reply = _call_model(

        _to_contents(
            conv["history"] + [new_message]
        ),

        system
    )


    # --------------------------------------------------------
    # Save ONLY after successful response
    # --------------------------------------------------------

    conv["history"] += [

        new_message,

        {
            "role": "model",
            "text": reply
        }

    ]


    return reply


# ============================================================
# RESET CONVERSATION
# ============================================================

def reset(conversation_id):

    """
    Delete conversation history.
    """

    conversations.pop(
        conversation_id,
        None
    )