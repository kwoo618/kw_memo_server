from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# 1. 데이터베이스 설정 (Docker 환경 변수에서 가져옴)
# localhost가 아닌 docker-compose의 서비스 이름('db')을 호스트로 사용해야 함
DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@db:3306/memodb")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. DB 모델 정의 (테이블)
class Memo(Base):
    __tablename__ = "memos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    content = Column(Text)

# 3. Pydantic 스키마 (데이터 검증)
class MemoCreate(BaseModel):
    title: str
    content: str

class MemoResponse(MemoCreate):
    id: int
    class Config:
        orm_mode = True

# 4. DB 테이블 생성 (앱 시작 시 자동 생성)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# DB 세션 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. API 엔드포인트
@app.post("/memos/", response_model=MemoResponse)
def create_memo(memo: MemoCreate, db: Session = Depends(get_db)):
    db_memo = Memo(title=memo.title, content=memo.content)
    db.add(db_memo)
    db.commit()
    db.refresh(db_memo)
    return db_memo

@app.get("/memos/", response_model=list[MemoResponse])
def read_memos(db: Session = Depends(get_db)):
    return db.query(Memo).all()