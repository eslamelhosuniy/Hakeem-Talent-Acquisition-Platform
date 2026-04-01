import os
import re
import logging
from fastapi import UploadFile, HTTPException, Request
from sqlalchemy import Column, Integer, String, create_engine, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger(__name__)


try:
    from controllers.TextExtractionController import TextExtractionController
    from controllers.NERController import NERController
except ImportError:
    from TextExtractionController import TextExtractionController
    from NERController import NERController


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
    
    candidate_name = Column(String, nullable=True)
    candidate_email = Column(String, nullable=True)
    candidate_phone = Column(String, nullable=True)
    candidate_skills = Column(Text, nullable=True)
    candidate_organizations = Column(Text, nullable=True)


Base.metadata.create_all(bind=engine)


UPLOAD_FOLDER = os.path.join(BASE_DIR, "assets", "files")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class DataController:

    @staticmethod
    async def create_cv(request: Request, job_title: str, file: UploadFile):
        db = SessionLocal()
        try:
            # أ. حفظ الملف
            from helpers.file_helper import generate_prefixed_filename
            clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
            filename = generate_prefixed_filename(clean_name)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)

            
            raw_text = ""
            try:
                raw_text = TextExtractionController.extract_text(
                    file_path=filepath,
                    generation_client=request.app.generation_client,
                    template_parser=request.app.template_parser
                )
                
               
                if raw_text is None:
                    raw_text = ""
                    logger.warning(f"VLM returned None for {filename}, using empty string.")
                    
            except Exception as e:
                
                logger.error(f"Extraction Step Failed: {str(e)}")
                raw_text = ""

           
            ner_data = NERController.process_text(raw_text)
            
            
            skills = ner_data.get("skills", [])
            skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
            
            orgs = ner_data.get("organizations", [])
            orgs_str = ", ".join(orgs) if isinstance(orgs, list) else str(orgs)

          
            ai_job = ner_data.get("job_title", "")
            display_job = f"{job_title} ({ai_job})" if ai_job != "Not Specified" else job_title

            
            new_cv = CVModel(
                job_title=display_job,
                cv_file=filename,
                candidate_name=ner_data.get("name", "Unknown"),
                candidate_email=ner_data.get("email", "Not Found"),
                candidate_phone=ner_data.get("phone", "Not Found"),
                candidate_skills=skills_str,
                candidate_organizations=orgs_str
            )
            
            db.add(new_cv)
            db.commit()
            db.refresh(new_cv)
            return new_cv
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error in create_cv: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
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
            result = db.query(CVModel).filter(CVModel.id == id).first()
            if not result:
                raise HTTPException(status_code=404, detail="CV not found")
            return result
        finally:
            db.close()

    @staticmethod
    async def update_cv(request: Request, id: int, job_title: str = None, file: UploadFile = None):
        db = SessionLocal()
        try:
            item = db.query(CVModel).filter(CVModel.id == id).first()
            if not item: 
                raise HTTPException(status_code=404, detail="CV not found")

            if job_title: 
                item.job_title = job_title

            if file:
              
                old_path = os.path.join(UPLOAD_FOLDER, item.cv_file)
                if os.path.exists(old_path): 
                    os.remove(old_path)

               
                from helpers.file_helper import generate_prefixed_filename
                filename = generate_prefixed_filename(re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename))
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                with open(filepath, "wb") as f:
                    f.write(await file.read())
                
              
                try:
                    raw_text = TextExtractionController.extract_text(
                        file_path=filepath,
                        generation_client=request.app.generation_client,
                        template_parser=request.app.template_parser
                    )
                    if raw_text is None: raw_text = ""
                except:
                    raw_text = ""

                ner_data = NERController.process_text(raw_text)
               

                skills = ner_data.get("skills", [])
                orgs = ner_data.get("organizations", [])
                ai_job = ner_data.get("job_title", "")
                
                item.cv_file = filename
                item.candidate_name = ner_data.get("name", "Unknown")
                item.candidate_email = ner_data.get("email", "Not Found")
                item.candidate_phone = ner_data.get("phone", "Not Found")
                item.candidate_skills = ", ".join(skills) if isinstance(skills, list) else str(skills)
                item.candidate_organizations = ", ".join(orgs) if isinstance(orgs, list) else str(orgs)
                
                if ai_job != "Not Specified":
                    base_title = job_title if job_title else item.job_title
                    item.job_title = f"{base_title} ({ai_job})"

            db.commit()
            db.refresh(item)
            return item
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()

    @staticmethod
    def delete(id: int):
        db = SessionLocal()
        try:
            item = db.query(CVModel).filter(CVModel.id == id).first()
            if not item:
                raise HTTPException(status_code=404, detail="CV not found")
            
            file_path = os.path.join(UPLOAD_FOLDER, item.cv_file)
            if os.path.exists(file_path): 
                os.remove(file_path)
                
            db.delete(item)
            db.commit()
            return {"message": f"CV deleted successfully"}
        finally:
            db.close()
            