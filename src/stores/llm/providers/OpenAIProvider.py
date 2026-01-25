from ..LLMInterface import LLMInterface


class OpenAIProvider(LLMInterface):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_text(self, prompt: str):
        # TODO: Implement
        pass

    def embed_text(self, text: str):
        # TODO: Implement
        pass
