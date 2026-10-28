"""Tenant and white-label settings."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenants"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    is_platform_tenant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="tenants")
    white_label: Mapped[Optional["WhiteLabelSettings"]] = relationship(
        "WhiteLabelSettings",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"


class WhiteLabelSettings(Base, TimestampMixin):
    __tablename__ = "white_label_settings"

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    product_display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    primary_color: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    accent_color: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    default_locale: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    support_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    support_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    custom_css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_footer_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="white_label")
