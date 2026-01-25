from abc import ABC, abstractmethod


class VectorDBInterface(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def insert_many(self, collection_name: str, texts: list, vectors: list):
        pass

    @abstractmethod
    def search_by_vector(self, collection_name: str, vector: list, limit: int):
        pass
