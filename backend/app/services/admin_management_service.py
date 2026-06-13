from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.admin_management import AdminManagedItem
from app.schemas.admin_management import (
    AdminManagedItemCreate,
    ManagedInternshipOpportunityListRead,
    ManagedInternshipOpportunityRead,
    AdminManagedItemPageRead,
    AdminManagedItemRead,
    AdminManagedItemStatus,
    AdminManagedItemType,
    AdminManagedItemUpdate,
)


class AdminManagementService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_items(
        self,
        *,
        item_type: AdminManagedItemType | None = None,
        status: AdminManagedItemStatus | None = None,
    ) -> AdminManagedItemPageRead:
        stmt: Select[tuple[AdminManagedItem]] = select(AdminManagedItem)
        count_stmt = select(func.count(AdminManagedItem.id))
        if item_type:
            stmt = stmt.where(AdminManagedItem.item_type == item_type)
            count_stmt = count_stmt.where(AdminManagedItem.item_type == item_type)
        if status:
            stmt = stmt.where(AdminManagedItem.status == status)
            count_stmt = count_stmt.where(AdminManagedItem.status == status)
        stmt = stmt.order_by(AdminManagedItem.item_type, AdminManagedItem.title)
        items = self.db.scalars(stmt).all()
        total = int(self.db.scalar(count_stmt) or 0)
        return AdminManagedItemPageRead(
            items=[AdminManagedItemRead.model_validate(item) for item in items],
            total=total,
        )

    def create_item(
        self,
        payload: AdminManagedItemCreate,
        *,
        user_id: int,
    ) -> AdminManagedItemRead:
        row = AdminManagedItem(
            item_type=payload.item_type,
            slug=payload.slug,
            title=payload.title,
            summary=payload.summary,
            status=payload.status,
            payload=payload.payload,
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )
        self.db.add(row)
        self._commit_or_raise_duplicate()
        self.db.refresh(row)
        return AdminManagedItemRead.model_validate(row)

    def update_item(
        self,
        item_id: int,
        payload: AdminManagedItemUpdate,
        *,
        user_id: int,
    ) -> AdminManagedItemRead:
        row = self._get_row(item_id)
        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(row, key, value)
        row.updated_by_user_id = user_id
        self._commit_or_raise_duplicate()
        self.db.refresh(row)
        return AdminManagedItemRead.model_validate(row)

    def archive_item(self, item_id: int, *, user_id: int) -> AdminManagedItemRead:
        row = self._get_row(item_id)
        row.status = "inactive"
        row.updated_by_user_id = user_id
        self.db.commit()
        self.db.refresh(row)
        return AdminManagedItemRead.model_validate(row)

    def list_active_internship_opportunities(
        self,
    ) -> ManagedInternshipOpportunityListRead:
        rows = self.db.scalars(
            select(AdminManagedItem)
            .where(AdminManagedItem.item_type == "internship_opportunity")
            .where(AdminManagedItem.status == "active")
            .order_by(AdminManagedItem.title)
        ).all()
        items = [self._internship_read(row) for row in rows]
        return ManagedInternshipOpportunityListRead(items=items, total=len(items))

    def _get_row(self, item_id: int) -> AdminManagedItem:
        row = self.db.get(AdminManagedItem, item_id)
        if row is None:
            raise ValueError("Managed item not found")
        return row

    def _commit_or_raise_duplicate(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Managed item slug already exists for this type") from exc

    def _internship_read(
        self,
        row: AdminManagedItem,
    ) -> ManagedInternshipOpportunityRead:
        payload = row.payload or {}
        return ManagedInternshipOpportunityRead(
            id=row.id,
            slug=row.slug,
            title=row.title,
            summary=row.summary,
            company=_optional_str(payload.get("company")),
            location=_optional_str(payload.get("location")),
            duration=_optional_str(payload.get("duration")),
            skills=_string_list(payload.get("skills")),
            eligibility=_string_list(payload.get("eligibility")),
            apply_url=_optional_str(payload.get("apply_url")),
            deadline=_optional_str(payload.get("deadline")),
            payload=payload,
        )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
