from datetime import datetime, timedelta
from sqlalchemy import (
    Boolean,
    Column,
    String,
    DateTime,
    create_engine,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv
import os
import pytz


load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL", ""))

Base = declarative_base()

MAGIC_LINK_EXPIRY = timedelta(hours=1)


db_session = sessionmaker(bind=engine)
db = db_session()

TZ = pytz.timezone("Africa/Casablanca")


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(TZ))

    magic_links = relationship("MagicLink", backref="user")

    def __repr__(self):
        return f"User(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, email={self.email}, created_at={self.created_at})"

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "created_at": str(self.created_at),
        }


class MagicLink(Base):
    __tablename__ = "magic_links"
    code = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    consumed = Column(Boolean, default=False)
    expires_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(TZ) + MAGIC_LINK_EXPIRY,
    )

    def __repr__(self):
        return f"MagicLink(code={self.code}, user_id={self.user_id}, expires_at={self.expires_at}, consumed={self.consumed})"

    def to_dict(self):
        return {
            "code": self.code,
            "user_id": self.user_id,
            "expires_at": str(self.expires_at),
            "consumed": self.consumed,
        }


Base.metadata.create_all(engine)
