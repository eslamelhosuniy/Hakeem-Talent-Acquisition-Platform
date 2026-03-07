import os
from fastapi import UploadFile
from helpers.file_helper import generate_prefixed_filename

UPLOAD_FOLDER = "src/assets/files"

data_store = []
counter = 1


class DataController:

    @staticmethod
    async def create_cv(job_title: str, file: UploadFile):

        global counter

        filename = generate_prefixed_filename(file.filename)

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        record = {
            "id": counter,
            "job_title": job_title,
            "cv_file": filename
        }

        data_store.append(record)

        counter += 1

        return record

    @staticmethod
    def get_all():

        return data_store

    @staticmethod
    def get_one(id: int):

        for item in data_store:
            if item["id"] == id:
                return item

        return None

    @staticmethod
    def delete(id: int):

        global data_store

        data_store = [item for item in data_store if item["id"] != id]

        return {"message": "Deleted successfully"}