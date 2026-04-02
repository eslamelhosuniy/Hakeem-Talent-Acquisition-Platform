import os
import re
import json
import sys
from fastapi import UploadFile
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


from helpers.config import settings


DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CVModel(Base):
    __tablename__ = "cvs"
  
    id = Column(Integer, primary_key=True, index=True) 
    job_title = Column(String, nullable=False)
    cv_file = Column(String, nullable=True)
    candidate_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    skills = Column(Text, nullable=True)
    raw_ner_json = Column(Text, nullable=True)


Base.metadata.create_all(bind=engine)


SRC_DIR = os.path.dirname(settings.DB_PATH)
UPLOAD_FOLDER = os.path.join(SRC_DIR, "assets", "files")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class DataController:

    @staticmethod
    async def create_cv(file: UploadFile, job_title: str, ner_results: dict = None):
        db = SessionLocal()
        try:
        
            filename = "None"
            if file:
                clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
                try:
                    from helpers.file_helper import generate_prefixed_filename
                    filename = generate_prefixed_filename(clean_name)
                except ImportError:
                    filename = f"cv_{clean_name}"
                
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                content = await file.read()
                with open(filepath, "wb") as f:
                    f.write(content)

           
            c_name = c_email = c_phone = c_skills = None
            if ner_results and "entities" in ner_results:
                ents = ner_results.get("entities", {})
                
            
                def get_val(key):
                    val = ents.get(key)
                    if isinstance(val, list) and len(val) > 0:
                        return val[0]
                    return val if val else None

                c_name = get_val("person")
                c_email = get_val("email")
                c_phone = get_val("phone")
                
                skills_list = ents.get("skills", [])
                c_skills = ", ".join(skills_list) if isinstance(skills_list, list) else str(skills_list)

           
            new_cv = CVModel(
                job_title=job_title,
                cv_file=filename,
                candidate_name=c_name,
                email=c_email,
                phone=c_phone,
                skills=c_skills,
                raw_ner_json=json.dumps(ner_results, ensure_ascii=False) if ner_results else None
            )
            
            db.add(new_cv)
            db.commit()
            db.refresh(new_cv)
            return new_cv
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
    def search_cvs(query: str):
        db = SessionLocal()
        try:
            search_filter = f"%{query}%"
            return db.query(CVModel).filter(
                (CVModel.candidate_name.like(search_filter)) |
                (CVModel.email.like(search_filter)) |
                (CVModel.skills.like(search_filter)) |
                (CVModel.job_title.like(search_filter))
            ).all()
        finally:
            db.close()

    @staticmethod
    def delete(id: int):
        db = SessionLocal()
        try:
            item = db.query(CVModel).filter(CVModel.id == id).first()
            if item:
                if item.cv_file and item.cv_file != "None":
                    file_path = os.path.join(UPLOAD_FOLDER, item.cv_file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                db.delete(item)
                db.commit()
                return {"message": "Deleted successfully"}
            return {"error": "CV not found"}
        finally:
            db.close()