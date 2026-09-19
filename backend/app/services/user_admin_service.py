"""Business logic dùng chung khi Admin/Manager cấp tài khoản."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import AdminCreateUserRequest, ManagerCreateUserRequest
from app.schemas.user import UserStatusRequest
from sqlalchemy import select, text
from app.services.audit_service import record_event
from app.services.account_control_service import ACCOUNT_CONTROL_LOCK, lock_active_actor


def set_user_status(db: Session, *, actor: User, user_id: int, data: UserStatusRequest) -> User:
    # Serialize status transitions, including cross-suspension of two admins.
    expected_actor_version = actor.token_version
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": ACCOUNT_CONTROL_LOCK})
    current_actor = db.execute(select(User).where(User.id == actor.id)
                              .execution_options(populate_existing=True)).scalar_one()
    if (current_actor.status != "active" or current_actor.role != "admin"
            or current_actor.token_version != expected_actor_version):
        raise HTTPException(status_code=403, detail="Tài khoản quản trị không còn hoạt động")
    target = db.execute(select(User).where(User.id == user_id).with_for_update()
                        .execution_options(populate_existing=True)).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    if data.status == "suspended" and target.id == actor.id:
        raise HTTPException(status_code=409, detail="Không được tự khóa tài khoản quản trị")
    if target.status == data.status:
        return target
    if target.role == "admin" and data.status == "suspended":
        active_count = db.query(User).filter(User.role == "admin", User.status == "active").count()
        if active_count <= 1:
            raise HTTPException(status_code=409, detail="Không được khóa Admin hoạt động cuối cùng")
    previous = target.status
    target.status = data.status
    target.token_version += 1
    record_event(db, actor_id=actor.id, action="user.status_changed", resource_type="user",
                 resource_id=target.id, details={"from": previous, "to": data.status, "reason": data.reason})
    db.commit()
    db.refresh(target)
    return target

ProvisionRequest = AdminCreateUserRequest | ManagerCreateUserRequest


def create_user_by(
    db: Session,
    *,
    creator: User,
    data: ProvisionRequest,
    role: str,
) -> User:
    """Tạo user có ``created_by`` và role do service quyết định."""
    creator = lock_active_actor(db, creator, {"admin", "manager"})
    if not (
        (creator.role == "admin" and role in {"technician", "manager"})
        or (creator.role == "manager" and role == "user")
    ):
        raise HTTPException(status_code=403, detail="Không được cấp vai trò này")
    if role not in {"user", "technician", "manager"}:
        raise ValueError(f"Role cấp tài khoản không hợp lệ: {role}")

    if user_crud.get_user_by_username(db, data.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username đã tồn tại trên hệ thống",
        )

    email_value = str(data.email) if data.email is not None else None
    if email_value and user_crud.get_user_by_email(db, email_value) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký trên hệ thống",
        )

    user = User(
        username=data.username,
        email=email_value,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=role,
        created_by=creator.id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username hoặc email đã tồn tại trên hệ thống",
        ) from exc
    db.refresh(user)
    return user


def list_users_for_admin(
    db: Session,
    *,
    role: str | None,
    limit: int = 50,
    offset: int = 0,
) -> list[User]:
    """Admin xem danh sách tài khoản hệ thống, có thể lọc role."""
    return user_crud.get_users(db, role=role, limit=limit, offset=offset)


def list_managed_users(db: Session, *, manager_id: int, limit: int = 50, offset: int = 0) -> list[User]:
    """Manager chỉ xem các User do chính mình tạo."""
    return user_crud.get_users(db, role="user", created_by=manager_id, limit=limit, offset=offset)
