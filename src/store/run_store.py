"""
Persistence for completed runs.

Separate from memory_store because the failure modes differ. Memory
failing silently is acceptable - the interview just repeats itself.
A run failing to save loses the only record of what the system did,
so it is logged loudly, but it still never raises: the user has their
post, and losing analytics is not worth losing that.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.db.base import SessionLocal
from src.db.models import Brief, Post, User
from src.schemas.perspective import Answer, PerspectiveBrief


def save_brief(
    user_id: str,
    brief: PerspectiveBrief,
    answers: list[Answer],
    was_probed: bool = False,
) -> uuid.UUID | None:
    """Persist a completed interview. Returns the brief id to pass to
    save_run, or None if saving failed."""
    try:
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.external_id == user_id))

            if user is None:
                user = User(external_id=user_id)
                session.add(user)
                session.flush()

            row = Brief(
                user_id=user.id,
                topic=brief.topic,
                payload=brief.model_dump(),
                answers=[a.model_dump() for a in answers],
                is_thin=brief.is_thin(),
                was_probed=was_probed,
            )
            session.add(row)
            session.commit()
            return row.id

    except SQLAlchemyError as exc:
        print(f"[run_store] failed to save brief: {exc}")
        return None


def save_run(brief_id: uuid.UUID | None, result: dict) -> None:
    """
    Persist a workflow result.

    Takes the raw LangGraph state and flattens the Verdict dataclass into
    columns. Accepts a None brief_id so a failed brief save degrades to a
    skipped run save rather than an exception.
    """
    if brief_id is None:
        return

    verdict = result.get("verdict")
    decision = result.get("decision")
    evaluation = result.get("evaluation")

    try:
        with SessionLocal() as session:
            session.add(Post(
                brief_id=brief_id,
                final_post=result.get("post", ""),
                craft_score=verdict.craft_score if verdict else None,
                faithfulness=verdict.faithfulness if verdict else None,
                passed_gate=verdict.passes_faithfulness if verdict else None,
                iterations=result.get("iteration", 0),
                best_iteration=result.get("best_iteration", 0),
                repairs_used=result.get("repairs_used", 0),
                stop_reason=decision.reason if decision else "",
                # --- FIX: Safely check if evaluation is a Pydantic model or a raw dict ---
                evaluation=evaluation.model_dump() if hasattr(evaluation, "model_dump") else (evaluation if evaluation else None),
            ))
            session.commit()

    except SQLAlchemyError as exc:
        print(f"[run_store] failed to save run: {exc}")