"""SQLAlchemy models — import all so Alembic can discover them."""

from app.models.organization import MemberRole, Organization, OrganizationMember
from app.models.tenant import Tenant, WhiteLabelSettings
from app.models.user import User
from app.models.video import (
    Project,
    SourceStatus,
    SourceType,
    Transcript,
    VideoMetadata,
    VideoSource,
)
from app.models.audit import (
    ActionItem,
    AuditFinding,
    AuditJob,
    AuditResult,
    JobStatus,
    SeoRecommendation,
    Severity,
)
from app.models.usage import AIUsageRecord
from app.models.contact import ContactLead
from app.models.billing import (
    OAuthToken,
    PaymentTransaction,
    PaymentWebhookEvent,
    PlanPrice,
    Subscription,
    SubscriptionPlan,
)

__all__ = [
    "User",
    "Organization",
    "OrganizationMember",
    "MemberRole",
    "Tenant",
    "WhiteLabelSettings",
    "Project",
    "VideoSource",
    "VideoMetadata",
    "Transcript",
    "SourceType",
    "SourceStatus",
    "AuditJob",
    "AuditResult",
    "AuditFinding",
    "SeoRecommendation",
    "ActionItem",
    "JobStatus",
    "Severity",
    "AIUsageRecord",
    "SubscriptionPlan",
    "PlanPrice",
    "Subscription",
    "PaymentTransaction",
    "PaymentWebhookEvent",
    "OAuthToken",
    "ContactLead",
]
