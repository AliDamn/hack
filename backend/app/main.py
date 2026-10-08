import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from . import llm, models, schemas
from .database import Base, SessionLocal, engine, get_db
from .seed import seed

ANALYSIS_STEPS = [
    "Classifying dispute type...",
    "Matching transactions...",
    "Checking network rules...",
    "Calculating risk score...",
    "Generating decision...",
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="ClaimAI API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"]
    + [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_case(db: Session, case_id: str) -> models.DisputeCase:
    case = db.scalar(
        select(models.DisputeCase)
        .options(selectinload(models.DisputeCase.transactions))
        .where(models.DisputeCase.id == case_id)
    )
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/cases", response_model=list[schemas.CaseSummary])
def list_cases(db: Session = Depends(get_db)):
    return db.scalars(select(models.DisputeCase).order_by(models.DisputeCase.position)).all()


@app.get("/api/cases/{case_id}", response_model=schemas.CaseDetail)
def get_case(case_id: str, db: Session = Depends(get_db)):
    return _get_case(db, case_id)


@app.post("/api/cases/{case_id}/analyze", response_model=schemas.Decision)
def analyze_case(
    case_id: str,
    body: schemas.AnalyzeRequest | None = None,
    db: Session = Depends(get_db),
):
    case = _get_case(db, case_id)
    operator_id = (body or schemas.AnalyzeRequest()).operator_id
    try:
        result = llm.analyze_dispute(
            case.id,
            case.complaint,
            [
                {"merchant": t.merchant, "amount": t.amount, "date": t.date, "auth": t.auth, "channel": t.channel}
                for t in case.transactions
            ],
        )
    except llm.LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    db.add(
        models.AuditEntry(
            case_id=case.id,
            operator_id=operator_id,
            decision=result["decision"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
        )
    )
    db.commit()
    return schemas.Decision(case_id=case.id, steps=ANALYSIS_STEPS, **result)


@app.get("/api/audit", response_model=list[schemas.AuditEntryOut])
def audit_log(limit: int = 50, db: Session = Depends(get_db)):
    return db.scalars(
        select(models.AuditEntry).order_by(models.AuditEntry.id.desc()).limit(min(limit, 500))
    ).all()
