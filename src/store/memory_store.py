"""
Postgres-backed user memory.

Same four functions as the JSON version, same signatures, same guarantee:
a storage failure never stops someone writing a post. The worst case is an
interview that asks something it has asked before.
"""
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from src.db.base import SessionLocal
from src.db.models import Memory, User
from src.schemas.perspective import UserMemory

# How many items of each kind to load. The database keeps everything; this
# caps what reaches the prompt. Replaces the list slicing in absorb().
RECALL_LIMIT = 20
embedder = NVIDIAEmbeddings(model="nvidia/llama-nemotron-embed-1b-v2")


def _kind_contents(session, user_id, kind: str, limit: int) -> list[str]:
    """Most recent items of one kind, returned oldest-first so the prompt
    reads chronologically."""
    rows = session.scalars(
        select(Memory.content)
        .where(Memory.user_id == user_id, Memory.kind == kind)
        .order_by(Memory.embedding.cosine_distance(search_vector))
        .limit(limit)
    ).all()
    return list(rows)


def get_memory(user_id: str) -> UserMemory:
    """
    Load one user's memory. Always returns a UserMemory.

    An unknown user gets an empty object with interviews_done = 0, so
    to_prompt_block() emits the first-interview message. Callers never
    need to check for None.
    """
    try:

        search_vector = embedder.embed_query(current_topic)
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.external_id == user_id))

            if user is None:
                return UserMemory(user_id=user_id)

            return UserMemory(
                user_id=user_id,
                known_views=_kind_contents(session, user.id, "view", RECALL_LIMIT),
                known_experiences=_kind_contents(session, user.id, "experience", RECALL_LIMIT),
                past_topics=_kind_contents(session, user.id, "topic", 50),
                audience=user.audience or "",
                interviews_done=user.interviews_done,
            )

    except SQLAlchemyError as exc:
        print(f"[memory_store] read failed, continuing without memory: {exc}")
        logging.exception("Memory read failed continuing without memory: {exc}")
        return UserMemory(user_id=user_id)


def save_memory(memory: UserMemory) -> None:
    """
    Persist one user's memory.

    Items are inserted with ON CONFLICT DO NOTHING rather than the store
    being replaced, so two sessions finishing an interview at the same
    moment cannot overwrite each other. The read-modify-write lock the
    JSON version needed is gone - the unique constraint does that job.
    """
    try:
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.external_id == memory.user_id))

            if user is None:
                user = User(external_id=memory.user_id)
                session.add(user)
                session.flush()

            user.audience = memory.audience or user.audience
            user.interviews_done = memory.interviews_done

            rows = [
                {"user_id": user.id, "kind": kind, "content": content}
                for kind, items in (
                    ("view", memory.known_views),
                    ("experience", memory.known_experiences),
                    ("topic", memory.past_topics),
                )
                for content in items
                if content.strip()
            ]

            if rows:
                texts_to_embed = [row["content"] for row in rows]
                vectors = embedder.embed_documents(texts_to_embed)
                for row, vector in zip(rows, vectors):
                    row["embedding"] = vector
                session.execute(
                    insert(Memory).values(rows).on_conflict_do_nothing(
                        constraint="memory_unique"
                    )
                )

            session.commit()

    except SQLAlchemyError as exc:
        print(f"[memory_store] write failed, memory not saved: {exc}")

"""

"""
def reset_memory(user_id: str) -> None:
    """Clear one user's memory. Cascade deletes the memory rows."""
    try:
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.external_id == user_id))
            if user:
                session.execute(select(Memory).where(Memory.user_id == user.id).delete())
                session.commit()
    except SQLAlchemyError as exc:
        print(f"[memory_store] reset failed: {exc}")