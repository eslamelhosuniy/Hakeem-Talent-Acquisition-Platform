from openai import OpenAI
from ..LLMInterface import LLMInterface


class OpenAIProvider(LLMInterface):
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.openai.com/v1",
        default_input_max_characters: int = 4096,
        default_generation_max_output_tokens: int = 2000,
        default_generation_temperature: float = 0.1,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
