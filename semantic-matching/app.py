import sys
from pathlib import Path

# Add parent directory to path for common imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from .models import MatchRequest, MatchResponse
from .service import SemanticMatchService

app = FastAPI(title="Semantic Matching Service", version="0.1.0")
svc = SemanticMatchService()


@app.get("/health")
def health():
    return {"status": "healthy", "service": "semantic-matching"}


@app.post("/semantic-match", response_model=MatchResponse)
def semantic_match(req: MatchRequest) -> MatchResponse:
    try:
        return svc.match(req)
    except Exception as exc:  # noqa: BLE001 - surface clean message
        raise HTTPException(status_code=500, detail=str(exc)) from exc

