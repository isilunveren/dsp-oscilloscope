import ssl
import os
import certifi
from openai import OpenAI, DefaultHttpxClient
from PySide6.QtCore import QThread, Signal
from app.llm.tools import TOOLS


class LLMWorker(QThread):

    result_ready = Signal(object)
    error = Signal(str)

    def __init__(self, client: OpenAI, model: str, messages: list, parent=None):
        super().__init__(parent)
        self.client = client
        self.model = model
        self.messages = messages

    def run(self):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            self.result_ready.emit(response.choices[0].message)
        except Exception as exc:
            self.error.emit(str(exc))


def create_nvidia_client() -> OpenAI:
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable is not set.")

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    return OpenAI(
        api_key=api_key,
        base_url="https://integrate.api.nvidia.com/v1",
        http_client=DefaultHttpxClient(verify=ssl_context),
    )