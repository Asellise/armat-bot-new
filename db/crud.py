from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, ScheduleItem, EnrollmentRequest


# ── Users ──────────────────────────────────────────────────────────────────────

async def get_or_create_user(session: AsyncSession, user_id: int, username: str | None, first_name: str) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=user_id, username=username, first_name=first_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return list(result.scalars().all())


# ── Schedule ───────────────────────────────────────────────────────────────────

async def get_schedule_by_day(session: AsyncSession, day: int) -> list[ScheduleItem]:
    result = await session.execute(
        select(ScheduleItem)
        .where(ScheduleItem.day_of_week == day, ScheduleItem.active == True)
        .order_by(ScheduleItem.time)
    )
    return list(result.scalars().all())


async def get_schedule_by_direction(session: AsyncSession, direction: str) -> list[ScheduleItem]:
    result = await session.execute(
        select(ScheduleItem)
        .where(ScheduleItem.direction == direction, ScheduleItem.active == True)
        .order_by(ScheduleItem.day_of_week, ScheduleItem.time)
    )
    return list(result.scalars().all())


async def get_all_schedule(session: AsyncSession) -> list[ScheduleItem]:
    result = await session.execute(
        select(ScheduleItem).order_by(ScheduleItem.day_of_week, ScheduleItem.time)
    )
    return list(result.scalars().all())


async def get_active_directions(session: AsyncSession) -> list[str]:
    result = await session.execute(
        select(ScheduleItem.direction)
        .where(ScheduleItem.active == True)
        .distinct()
        .order_by(ScheduleItem.direction)
    )
    return list(result.scalars().all())


async def get_schedule_item(session: AsyncSession, item_id: int) -> ScheduleItem | None:
    result = await session.execute(select(ScheduleItem).where(ScheduleItem.id == item_id))
    return result.scalar_one_or_none()


async def create_schedule_item(
    session: AsyncSession,
    day_of_week: int,
    time: str,
    direction: str,
    teacher: str,
    duration_minutes: int = 60,
) -> ScheduleItem:
    item = ScheduleItem(
        day_of_week=day_of_week,
        time=time,
        direction=direction,
        teacher=teacher,
        duration_minutes=duration_minutes,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_schedule_item(session: AsyncSession, item_id: int, **kwargs) -> None:
    await session.execute(
        update(ScheduleItem).where(ScheduleItem.id == item_id).values(**kwargs)
    )
    await session.commit()


async def delete_schedule_item(session: AsyncSession, item_id: int) -> None:
    await session.execute(delete(ScheduleItem).where(ScheduleItem.id == item_id))
    await session.commit()


# ── Enrollment Requests ────────────────────────────────────────────────────────

async def create_enrollment_request(
    session: AsyncSession,
    user_id: int,
    name: str,
    phone: str,
    direction: str,
    message: str | None = None,
) -> EnrollmentRequest:
    req = EnrollmentRequest(
        user_id=user_id,
        name=name,
        phone=phone,
        direction=direction,
        message=message,
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req


async def get_enrollment_requests(session: AsyncSession, status: str | None = None) -> list[EnrollmentRequest]:
    q = select(EnrollmentRequest).order_by(EnrollmentRequest.created_at.desc())
    if status:
        q = q.where(EnrollmentRequest.status == status)
    result = await session.execute(q)
    return list(result.scalars().all())


async def mark_enrollment_seen(session: AsyncSession, req_id: int) -> None:
    await session.execute(
        update(EnrollmentRequest).where(EnrollmentRequest.id == req_id).values(status="seen")
    )
    await session.commit()
