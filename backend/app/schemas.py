from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    merchant: str
    amount: str
    date: str
    auth: str
    channel: str


class CaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chip: str


class CaseDetail(CaseSummary):
    complaint: str
    transactions: list[TransactionOut]


class Decision(BaseModel):
    case_id: str
    type: str
    decision: str
    decision_class: str
    risk: int
    confidence: int
    reasoning: str
    actions: list[str]
    letter: str
    steps: list[str]


class AnalyzeRequest(BaseModel):
    operator_id: str = "demo-operator"


class AuditEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    operator_id: str
    decision: str
    confidence: int
    reasoning: str
    created_at: datetime
