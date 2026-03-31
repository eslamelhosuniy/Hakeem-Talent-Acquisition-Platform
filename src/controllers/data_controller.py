import os
import re
from fastapi import UploadFile
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CVModel(Base):
    __tablename__ = "cvs"
  
    id = Column(Integer, primary_key=True, index=True) 
    job_title = Column(String)
    cv_file = Column(String)

Base.metadata.create_all(bind=engine)


UPLOAD_FOLDER = os.path.join(BASE_DIR, "assets", "files")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class DataController:
    @staticmethod
    async def create_cv(job_title: str, file: UploadFile):
        db = SessionLocal()
        try:
            from helpers.file_helper import generate_prefixed_filename
            clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
            filename = generate_prefixed_filename(clean_name)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)

            new_cv = CVModel(job_title=job_title, cv_file=filename)
            db.add(new_cv)
            db.commit()
            db.refresh(new_cv)
            return new_cv
        finally:
            db.close()

    @staticmethod
    async def update_cv(id: int, job_title: str = None, file: UploadFile = None):
        db = SessionLocal()
        try:
            item = db.query(CVModel).filter(CVModel.id == id).first()
            if not item:
                return {"error": "CV not found"}

            if job_title:
                item.job_title = job_title

            if file:
               
                old_path = os.path.join(UPLOAD_FOLDER, item.cv_file)
                if os.path.exists(old_path):
                    os.remove(old_path)

              
                from helpers.file_helper import generate_prefixed_filename
                clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
                filename = generate_prefixed_filename(clean_name)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                with open(filepath, "wb") as f:
                    content = await file.read()
                    f.write(content)
                item.cv_file = filename

            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    @staticmethod
    def get_all():
        db = SessionLocal()
        try:
            return db.query(CVModel).all()
        finally:
            db.close()

    @staticmethod
    def get_one(id: int):
        db = SessionLocal()
        try:
            return db.query(CVModel).filter(CVModel.id == id).first()
        finally:
            db.close()

    @staticmethod
    def delete(id: int):
        db = SessionLocal()
        try:
            item = db.query(CVModel).filter(CVModel.id == id).first()
            if item:
                file_path = os.path.join(UPLOAD_FOLDER, item.cv_file)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.delete(item)
                db.commit()
                return {"message": "Deleted successfully"}
            return {"error": "CV not found"}
        finally:
            db.close()