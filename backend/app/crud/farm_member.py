"""CRUD thuần cho bảng farm_members."""

from sqlalchemy.orm import Session, joinedload

from app.models.farm_member import FarmMember


def get_members_by_farm(db: Session, farm_id: int) -> list[FarmMember]:
    """Lấy thành viên Farm và eager-load thông tin User."""
    return (
        db.query(FarmMember)
        .options(joinedload(FarmMember.user))
        .filter(FarmMember.farm_id == farm_id)
        .order_by(FarmMember.created_at.desc(), FarmMember.id.desc())
        .all()
    )


def get_membership(
    db: Session,
    *,
    farm_id: int,
    user_id: int,
) -> FarmMember | None:
    """Tìm membership theo khóa nghiệp vụ farm/user."""
    return (
        db.query(FarmMember)
        .filter(
            FarmMember.farm_id == farm_id,
            FarmMember.user_id == user_id,
        )
        .first()
    )
