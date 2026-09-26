from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Integer, String, DateTime, ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
    pass


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)

    method: Mapped[str] = mapped_column(String(10), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )


    logs: Mapped[list["MonitoringLog"]] = relationship(
        back_populates = "service"
    )


class MonitoringLog(Base):
    __tablename__ = "monitoring_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id"),
        nullable=False
    )

    status_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    response_time: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    is_healthy: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    service:Mapped[list["Service"]] = relationship(
        back_populates = "logs"
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user"
    )