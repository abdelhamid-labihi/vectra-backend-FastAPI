from datetime import datetime
import random

from orm import db, MagicLink, TZ


def generate_magic_number():
    return str(random.randint(111111, 999999))


def save_magic_number(user, magic_number):
    new_magic_number = MagicLink(
        code=magic_number,
        user_id=user.id,
        consumed=False,
    )
    db.add(new_magic_number)
    db.commit()


async def verify_magic_number(magic_number: str) -> bool:
    magic_number = db.query(MagicLink).filter_by(code=magic_number).first()
    if not magic_number:
        return False
    if (
        bool(magic_number.consumed)
        or magic_number.expires_at.timestamp() < datetime.now(TZ).timestamp()
    ):
        return False
    magic_number.consumed = True  # type: ignore
    db.commit()
    return True


async def confirm_user(
    magic_number: str,
):
    magic_number = db.query(MagicLink).filter_by(code=magic_number).first()
    if not magic_number:
        return None
    magic_number.consumed = True  # type: ignore
    magic_number.user.verified = True
    db.commit()
    return magic_number.user.email
