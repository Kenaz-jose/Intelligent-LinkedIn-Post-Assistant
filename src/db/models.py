import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Numeric, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB

from src.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # The id the app knows a user by ("demo-user", "cli-user", later a real
    # auth subject). Kept separate from the primary key so the internal id
    # never has to change when auth is introduced.
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    audience: Mapped[str] = mapped_column(Text, default="")
    interviews_done: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memories: Mapped[list["Memory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Memory(Base):
    """
    One remembered item. Rows rather than a JSON list, so memory can be
    ordered by recency, capped in SQL, and eventually filtered by
    embedding similarity instead of keyword overlap.
    """

    __tablename__ = "memories"
    __table_args__ = (
        CheckConstraint("kind IN ('view', 'experience', 'topic')", name="memory_kind"),
        # Deduplication moves into the database. absorb() still dedupes in
        # memory, but this makes a duplicate impossible even if two sessions
        # write concurrently.
        UniqueConstraint("user_id", "kind", "content", name="memory_unique"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped["User"] = relationship(back_populates="memories")


class Brief(Base):
    """
    One completed interview: the answers given and the perspective
    synthesised from them. Kept together because when a post comes out
    wrong, the first question is always whether the brief was wrong or
    the generator was - and that needs both.
    """

    __tablename__ = "briefs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    topic: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB)   # PerspectiveBrief.model_dump()
    answers: Mapped[list] = mapped_column(JSONB)   # [Answer.model_dump(), ...]

    # Denormalised so "do thin briefs produce worse posts?" is one query
    # rather than a JSONB extraction across every row.
    is_thin: Mapped[bool] = mapped_column(Boolean, default=False)
    was_probed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    posts: Mapped[list["Post"]] = relationship(
        back_populates="brief", cascade="all, delete-orphan"
    )


class Post(Base):
    """
    One workflow run. Scores are flat columns rather than JSONB because
    these are the questions actually worth asking of this table: does
    refinement ever win, how often does the gate fail, is craft trending.
    """

    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    brief_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("briefs.id", ondelete="CASCADE"), index=True
    )

    final_post: Mapped[str] = mapped_column(Text)

    craft_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    faithfulness: Mapped[int | None] = mapped_column(SmallInteger)
    passed_gate: Mapped[bool | None] = mapped_column(Boolean)

    iterations: Mapped[int] = mapped_column(SmallInteger, default=0)
    best_iteration: Mapped[int] = mapped_column(SmallInteger, default=0)
    repairs_used: Mapped[int] = mapped_column(SmallInteger, default=0)
    stop_reason: Mapped[str] = mapped_column(Text, default="")

    evaluation: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    brief: Mapped["Brief"] = relationship(back_populates="posts")