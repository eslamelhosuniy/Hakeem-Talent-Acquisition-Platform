import os
import re
from fastapi import UploadFile
from helpers.file_helper import generate_prefixed_filename

# تحديد المسار الرئيسي للمشروع
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# تحديد فولدر الحفظ: src/assets/files
UPLOAD_FOLDER = os.path.join(BASE_DIR, "assets", "files")

# التأكد أن الفولدر موجود، ولو مش موجود يكريته
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class DataController:
    # القائمة اللي بتخزن البيانات في الذاكرة (Memory)
    data_store = []
    counter = 1

    @staticmethod
    async def create_cv(job_title: str, file: UploadFile):
        # تنظيف اسم الملف من الحروف الغريبة
        clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
        filename = generate_prefixed_filename(clean_name)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # حفظ الملف فعلياً على الهارد
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        record = {
            "id": DataController.counter,
            "job_title": job_title,
            "cv_file": filename
        }
        DataController.data_store.append(record)
        DataController.counter += 1
        return record

    @staticmethod
    async def update_cv(id: int, job_title: str, file: UploadFile = None):
        for item in DataController.data_store:
            if item["id"] == id:
                if job_title:
                    item["job_title"] = job_title

                if file:
                    # 1. مسح الملف القديم قبل رفع الجديد لتوفير المساحة
                    old_path = os.path.join(UPLOAD_FOLDER, item["cv_file"])
                    if os.path.exists(old_path):
                        os.remove(old_path)

                    # 2. معالجة وحفظ الملف الجديد
                    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
                    filename = generate_prefixed_filename(clean_name)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                    with open(filepath, "wb") as f:
                        content = await file.read()
                        f.write(content)

                    item["cv_file"] = filename

                return item
        return {"error": "CV not found"}

    @staticmethod
    def get_all():
        return DataController.data_store

    @staticmethod
    def get_one(id: int):
        for item in DataController.data_store:
            if item["id"] == id:
                return item
        return None

    @staticmethod
    def delete(id: int):
      
        target_index = -1
        for i, item in enumerate(DataController.data_store):
            if item["id"] == id:
                target_index = i
                break

        if target_index != -1:
          
            filename = DataController.data_store[target_index]["cv_file"]
            file_path = os.path.join(UPLOAD_FOLDER, filename)

          
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

            
            DataController.data_store.pop(target_index)
            
            return {"message": f"CV with ID {id} and its file deleted successfully"}
        
        return {"error": "CV not found"}