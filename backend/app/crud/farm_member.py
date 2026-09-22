"""CRUD thuần cho bảng farm_members."""

from sqlalchemy.orm import Session, joinedload

from app.models.farm_member import FarmMember


def get_members_by_farm(db: Session, farm_id: int, *, limit: int = 50, offset: int = 0) -> list[FarmMember]:
    """Lấy thành viên Farm và eager-load thông tin User."""
    return (
        db.query(FarmMember)
        .options(joinedload(FarmMember.user))
        .filter(FarmMember.farm_id == farm_id)
        .order_by(FarmMember.created_at.desc(), FarmMember.id.desc())
        .offset(offset).limit(limit)
        .all()
    )


def get_membership(
    db: Session,
    *,
    farm_id: int,
    user_id: int,
    for_update: bool = False,
) -> FarmMember | None:
    """Tìm membership theo khóa nghiệp vụ farm/user."""
    query = (
        db.query(FarmMember)
        .filter(
            FarmMember.farm_id == farm_id,
            FarmMember.user_id == user_id,
        )
    )
    if for_update:
        query = query.populate_existing().with_for_update()
    return query.first()
