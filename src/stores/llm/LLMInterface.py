from abc import ABC, abstractmethod


class LLMInterface(ABC):

    @abstractmethod
    def generate_text(self, prompt: str):
        pass

    @abstractmethod
    def embed_text(self, text: str):
        pass
