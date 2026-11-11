import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.tracing import traced


load_dotenv()


class GeminiLLM:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in .env file"
            )

        timeout_ms = int(os.getenv("GEMINI_TIMEOUT_MS", "20000"))
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_ms)
        )

    @traced(name="parcelpilot.gemini_generation")
    def generate(self, prompt: str):

        max_attempts = 2

        for attempt in range(max_attempts):

            try:

                response = (
                    self.client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt
                    )
                )

                return response.text

            except Exception as e:

                error_message = str(e)

                # Quota / rate limit error
                if (
                    "429" in error_message
                    or "RESOURCE_EXHAUSTED"
                    in error_message
                ):

                    print(
                        "Gemini quota or rate limit reached."
                    )

                    raise RuntimeError(
                        "Gemini API quota exceeded."
                    )

                # Retry only transient rate-limit, server, or timeout failures.
                transient = any(code in error_message for code in (
                    "429", "500", "502", "503", "504",
                    "RESOURCE_EXHAUSTED", "UNAVAILABLE",
                    "DeadlineExceeded", "Timeout"
                ))
                if attempt == max_attempts - 1 or not transient:
                    raise RuntimeError(f"LLM request failed: {e}") from e

                wait_time = 1.5 * (attempt + 1)

                print(
                    f"LLM attempt {attempt + 1} failed. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)