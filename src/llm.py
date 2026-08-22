import os
import time

from dotenv import load_dotenv
from google import genai


load_dotenv()


class GeminiLLM:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in .env file"
            )

        self.client = genai.Client(
            api_key=api_key
        )

    def generate(self, prompt: str):

        max_attempts = 3

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

                # Last attempt
                if attempt == max_attempts - 1:

                    raise RuntimeError(
                        f"LLM request failed: {e}"
                    )

                wait_time = 3 * (
                    attempt + 1
                )

                print(
                    f"LLM attempt {attempt + 1} failed. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)