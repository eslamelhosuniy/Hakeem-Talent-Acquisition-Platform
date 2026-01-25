from ..VectorDBInterface import VectorDBInterface


class QdrantDBProvider(VectorDBInterface):
    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self):
        # TODO: Implement
        pass

    def insert_many(self, collection_name: str, texts: list, vectors: list):
        # TODO: Implement
        pass

    def search_by_vector(self, collection_name: str, vector: list, limit: int):
        # TODO: Implement
        pass
