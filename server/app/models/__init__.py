"""ORM models – import all so Alembic can discover them."""

from app.models.user import User
from app.models.student import Student
from app.models.subject import Subject
from app.models.knowledge import KnowledgeNode
from app.models.milestone import Milestone, MilestoneReminder
from app.models.action_card import ActionCard
from app.models.quote import DailyQuote, UserQuoteFavorite, UserQuoteHistory
from app.models.exam import Exam, ExamScore
from app.models.error_note import ErrorNote
from app.models.growth_record import GrowthRecord
from app.models.school_progress import SchoolProgress
from app.models.subscription import UserSubscription
from app.models.ai_chat import AIChatSession, AIChatMessage

__all__ = [
    "User",
    "Student",
    "Subject",
    "KnowledgeNode",
    "Milestone",
    "MilestoneReminder",
    "ActionCard",
    "DailyQuote",
    "UserQuoteFavorite",
    "UserQuoteHistory",
    "Exam",
    "ExamScore",
    "ErrorNote",
    "GrowthRecord",
    "SchoolProgress",
    "UserSubscription",
    "AIChatSession",
    "AIChatMessage",
]
