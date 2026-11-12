
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.tracing import traced


load_dotenv()


class GeminiLLM:

    def __init__(self):

        # Read local environment or Streamlit Cloud secrets.
        try:
            import streamlit as st

            secret_api_key = st.secrets.get(
                "GEMINI_API_KEY", ""
            )
            secret_timeout = st.secrets.get(
                "GEMINI_TIMEOUT_MS", "20000"
            )
            secret_primary = st.secrets.get(
                "GEMINI_MODEL", "gemini-3.8-flash"
            )
            secret_fallback = st.secrets.get(
                "GEMINI_FALLBACK_MODEL",
                "gemini-3.5-flash-lite"
            )

        except Exception:
            secret_api_key = ""
            secret_timeout = "20000"
            secret_primary = "gemini-3.8-flash"
            secret_fallback = "gemini-3.5-flash-lite"

        api_key = (
            os.getenv("GEMINI_API_KEY")
            or secret_api_key
        )

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing."
            )

        self.timeout_ms = int(
            os.getenv("GEMINI_TIMEOUT_MS")
            or secret_timeout
        )

        self.primary_model = (
            os.getenv("GEMINI_MODEL")
            or secret_primary
        )

        self.fallback_model = (
            os.getenv("GEMINI_FALLBACK_MODEL")
            or secret_fallback
        )

        if self.primary_model == self.fallback_model:
            raise ValueError(
                "Primary and fallback models must be different."
            )

        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=self.timeout_ms
            )
        )

    @traced(name="parcelpilot.gemini_generation")
    def generate(self, prompt: str):

        models = [
            self.primary_model,
            self.fallback_model,
        ]

        last_error = None

        for index, model_name in enumerate(models):

            start = time.perf_counter()

            try:

                print(
                    f"[LLM] Trying model: {model_name}"
                )

                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                elapsed = (
                    time.perf_counter() - start
                ) * 1000

                answer = response.text

                if not answer or not answer.strip():
                    raise RuntimeError(
                        f"{model_name} returned an empty response."
                    )

                print(
                    f"[PERF] {model_name}: {elapsed:.2f} ms"
                )

                if index == 1:
                    print(
                        "[LLM] Fallback model generated the response."
                    )

                return answer

            except Exception as error:

                last_error = error

                elapsed = (
                    time.perf_counter() - start
                ) * 1000

                error_message = str(error)

                print(
                    f"[LLM] {model_name} failed "
                    f"after {elapsed:.2f} ms: {error_message}"
                )

                # Only switch models for transient failures.
                transient = any(
                    code in error_message.lower()
                    for code in (
                        "429",
                        "500",
                        "502",
                        "503",
                        "504",
                        "resource_exhausted",
                        "unavailable",
                        "deadlineexceeded",
                        "timeout",
                        "temporarily",
                        "overloaded",
                    )
                )

                if not transient:
                    raise RuntimeError(
                        f"Non-retryable Gemini error: {error}"
                    ) from error

                if index == 0:
                    print(
                        f"[LLM] Switching to fallback: "
                        f"{self.fallback_model}"
                    )

        raise RuntimeError(
            "Both Gemini models failed. "
            f"Last error: {last_error}"
        ) from last_error
