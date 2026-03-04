from fastapi import APIRouter, Query
from backend.api.v1.endpoints.analyze import results_store

router = APIRouter()


@router.get("")
async def get_history(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Return analysis history from the in-memory store, newest first."""
    all_items = sorted(results_store.values(), key=lambda x: x.get("created_at", ""), reverse=True)
    page = all_items[offset : offset + limit]

    # Strip heavy data for list view
    items = []
    for r in page:
        items.append({
            "id": r.get("id"),
            "filename": r.get("original_filename", r.get("filename")),
            "file_type": r.get("file_type"),
            "score": r.get("score", r.get("aacs_score", 0)),
            "aacs_score": r.get("aacs_score", r.get("score", 0)),
            "verdict": r.get("verdict"),
            "verdict_color": r.get("verdict_color"),
            "created_at": r.get("created_at"),
            "elapsed_seconds": r.get("elapsed_seconds"),
        })

    return {"items": items, "total": len(all_items), "limit": limit, "offset": offset}