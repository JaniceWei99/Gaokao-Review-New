"""Seed data import script.

Usage: cd server && python seed.py
"""

import asyncio
import json
import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base

# Import all models
from app.models import *  # noqa: F401, F403
from app.models.subject import Subject
from app.models.knowledge import KnowledgeNode
from app.models.milestone import Milestone
from app.models.action_card import ActionCard
from app.models.quote import DailyQuote

SEEDS_DIR = Path(__file__).parent / "seeds"


async def seed_subjects(session: AsyncSession) -> None:
    """Load subjects from JSON."""
    data = json.loads((SEEDS_DIR / "subjects.json").read_text(encoding="utf-8"))
    for item in data:
        subject = Subject(
            id=item["id"],
            name=item["name"],
            category=item["category"],
            gaokao_max_score=item["gaokao_max_score"],
            display_order=item["display_order"],
            icon=item.get("icon", ""),
        )
        session.add(subject)
    await session.flush()
    print(f"  Loaded {len(data)} subjects")


async def seed_knowledge_tree(session: AsyncSession) -> None:
    """Load knowledge tree from per-subject JSON files."""
    kt_dir = SEEDS_DIR / "knowledge_tree"
    total = 0

    for json_file in sorted(kt_dir.glob("*.json")):
        subject_id = json_file.stem  # e.g., "math" from "math.json"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        count = await _load_nodes(session, subject_id, data, parent_id=None)
        total += count
        print(f"  Loaded {count} nodes for {subject_id}")

    print(f"  Total knowledge nodes: {total}")


async def _load_nodes(
    session: AsyncSession,
    subject_id: str,
    nodes: list[dict],
    parent_id: uuid.UUID | None,
) -> int:
    """Recursively load knowledge tree nodes."""
    count = 0
    for item in nodes:
        node_id = uuid.uuid4()
        node = KnowledgeNode(
            id=node_id,
            subject_id=subject_id,
            parent_id=parent_id,
            level=item["level"],
            name=item["name"],
            display_order=item["display_order"],
            is_active=True,
        )
        session.add(node)
        count += 1

        children = item.get("children", [])
        if children:
            count += await _load_nodes(session, subject_id, children, parent_id=node_id)

    return count


async def seed_milestones(session: AsyncSession) -> None:
    """Load system milestones from JSON."""
    data = json.loads((SEEDS_DIR / "milestones.json").read_text(encoding="utf-8"))
    for item in data:
        milestone = Milestone(
            id=uuid.uuid4(),
            type="system",
            student_id=None,
            title=item["title"],
            description=item.get("description"),
            event_date=date.fromisoformat(item["event_date"]),
            event_end_date=date.fromisoformat(item["event_end_date"]) if item.get("event_end_date") else None,
            category=item["category"],
            applicable_grades=item.get("applicable_grades", []),
            applicable_subjects=item.get("applicable_subjects"),
            applicable_districts=item.get("applicable_districts"),
            requires_jan_english=item.get("requires_jan_english", False),
            remind_15d=item.get("remind_15d", True),
            remind_3d=item.get("remind_3d", True),
            is_dynamic_date=item.get("is_dynamic_date", False),
            display_order=item.get("display_order", 0),
        )
        session.add(milestone)
    await session.flush()
    print(f"  Loaded {len(data)} milestones")


async def seed_action_cards(session: AsyncSession) -> None:
    """Load action cards from JSON."""
    data = json.loads((SEEDS_DIR / "action_cards.json").read_text(encoding="utf-8"))
    for item in data:
        card = ActionCard(
            id=uuid.uuid4(),
            milestone_category=item["milestone_category"],
            timing=item["timing"],
            title=item["title"],
            description=item.get("description"),
            action_items=item["action_items"],
            footer_tip=item.get("footer_tip"),
            applicable_grades=item.get("applicable_grades", []),
            applicable_subjects=item.get("applicable_subjects"),
            quote_category=item.get("quote_category"),
        )
        session.add(card)
    await session.flush()
    print(f"  Loaded {len(data)} action cards")


async def seed_quotes(session: AsyncSession) -> None:
    """Load daily quotes from JSON."""
    data = json.loads((SEEDS_DIR / "quotes.json").read_text(encoding="utf-8"))
    for i, item in enumerate(data):
        quote = DailyQuote(
            id=uuid.uuid4(),
            content=item["content"],
            author=item.get("author"),
            category=item["category"],
            applicable_grades=item.get("applicable_grades", ["gao1", "gao2", "gao3"]),
            applicable_phase=item.get("applicable_phase", "all"),
            display_order=item.get("display_order", i + 1),
            is_active=True,
        )
        session.add(quote)
    await session.flush()
    print(f"  Loaded {len(data)} quotes")


async def check_table_empty(session: AsyncSession, table_name: str) -> bool:
    """Check if a table is empty."""
    result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    count = result.scalar()
    return count == 0


async def main() -> None:
    """Run all seed operations."""
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        print("Seeding database...")

        # Only seed if tables are empty (idempotent)
        if await check_table_empty(session, "subjects"):
            print("\n[1/5] Seeding subjects...")
            await seed_subjects(session)
        else:
            print("\n[1/5] Subjects table not empty, skipping")

        if await check_table_empty(session, "knowledge_nodes"):
            print("\n[2/5] Seeding knowledge tree...")
            await seed_knowledge_tree(session)
        else:
            print("\n[2/5] Knowledge nodes table not empty, skipping")

        if await check_table_empty(session, "milestones"):
            print("\n[3/5] Seeding milestones...")
            await seed_milestones(session)
        else:
            print("\n[3/5] Milestones table not empty, skipping")

        if await check_table_empty(session, "action_cards"):
            print("\n[4/5] Seeding action cards...")
            await seed_action_cards(session)
        else:
            print("\n[4/5] Action cards table not empty, skipping")

        if await check_table_empty(session, "daily_quotes"):
            print("\n[5/5] Seeding quotes...")
            await seed_quotes(session)
        else:
            print("\n[5/5] Quotes table not empty, skipping")

        await session.commit()
        print("\nSeed complete!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
