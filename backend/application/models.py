from __future__ import annotations

from enum import StrEnum, Enum
from datetime import date, datetime
from decimal import Decimal

from .extensions import db, hash_password, verify_password


class UserRoleName(StrEnum):
	ADMIN = "admin"
	TREKKER = "trekker"
	TREK_STAFF = "trek_staff"


class TrekStatus(StrEnum):
	DRAFT = "draft"
	OPEN = "open"
	COMPLETED = "completed"
	CANCELLED = "cancelled"


class BookingStatus(StrEnum):
	BOOKED = "booked"
	CANCELLED = "cancelled"


from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class ExportMixin:
    """
    Mixin for exporting SQLAlchemy models to JSON-friendly dictionaries.
    """

    # Override in subclasses if desired.
    # Example:
    # extra_properties = ("seats_available", "is_full")
    extra_properties: tuple[str, ...] = ()

    @property
    def _columns(self) -> tuple[str, ...]:
        """Names of all mapped database columns."""
        return tuple(column.name for column in self.__table__.columns)

    @staticmethod
    def _serialize(value):
        """Convert common Python/SQLAlchemy types into JSON-friendly values."""

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        return value

    def export(self, *fields: str) -> dict[str, object]:
        """
        Export selected fields.

        If no fields are supplied:
            - export all mapped columns
            - export all properties listed in `extra_properties`
        """

        if not fields:
            data = {
                field: self._serialize(getattr(self, field))
                for field in self._columns
            }

            for prop in self.extra_properties:
                data[prop] = self._serialize(getattr(self, prop))

            return data

        allowed = set(self._columns) | set(self.extra_properties)

        invalid = set(fields) - allowed
        if invalid:
            raise ValueError(f"Unknown export fields: {sorted(invalid)}")

        return {
            field: self._serialize(getattr(self, field))
            for field in fields
        }

    def exclude(self, *fields: str) -> dict[str, object]:
        """
        Export every mapped column and extra property except the excluded ones.
        """

        allowed = tuple(self._columns) + tuple(self.extra_properties)

        invalid = set(fields) - set(allowed)
        if invalid:
            raise ValueError(f"Unknown excluded fields: {sorted(invalid)}")

        excluded = set(fields)

        return {
            field: self._serialize(getattr(self, field))
            for field in allowed
            if field not in excluded
        }
	
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
	return [member.value for member in enum_cls]


class TimestampMixin:
	created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
	updated_at = db.Column(
		db.DateTime,
		nullable=False,
		server_default=db.func.now(),
		onupdate=db.func.now(),
	)


class User(db.Model, TimestampMixin, ExportMixin):
	__tablename__ = "users"

	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(255), unique=True, nullable=False)
	password_hash = db.Column(db.String(255), nullable=False, default="dummy_password_hash", server_default="dummy_password_hash")
	first_name = db.Column(db.String(80), nullable=False)
	last_name = db.Column(db.String(80), nullable=True)
	is_active = db.Column(db.Boolean, nullable=False,
					   default=True, server_default=db.true())

	role = db.Column(
		db.Enum(
			UserRoleName,
			native_enum=False,
			create_constraint=True,
			validate_strings=True,
			values_callable=enum_values,
		),
		nullable=False,
		default=UserRoleName.TREKKER,
		server_default=UserRoleName.TREKKER.value
	)

	bookings = db.relationship(
		"Booking",
		back_populates="trekker",
		cascade="all, delete-orphan",
		foreign_keys="Booking.trekker_user_id",
		lazy="selectin",
	)

	__table_args__ = (
		db.CheckConstraint(
			"email LIKE '%@%.%'",
			name="ck_users_email_shape",
		),
		db.Index("ix_users_email", "email", "is_active"),
		db.Index("ix_users_role", "role", "is_active"),
		db.Index("ix_users_first_last_name", "first_name", "last_name"),
		db.Index("ix_users_is_active", "is_active"),
	)

	@property
	def is_admin(self) -> bool:
		return self.role == UserRoleName.ADMIN
	
	@property
	def is_trekker(self) -> bool:
		return self.role == UserRoleName.TREKKER
	
	@property
	def is_trek_staff(self) -> bool:
		return self.role == UserRoleName.TREK_STAFF
	
	@property
	def full_name(self) -> str:
		if self.last_name:
			return f"{self.first_name} {self.last_name}"
		return self.first_name

	def set_password(self, password: str) -> None:
		if not password:
			raise ValueError("Password cannot be empty")
		self.password_hash = hash_password(password)

	def check_password(self, password: str) -> bool:
		if not self.password_hash:
			return False
		return verify_password(password, self.password_hash)
	
	def make_staff(self):
		self.role = UserRoleName.TREK_STAFF

	def __repr__(self) -> str:
		return f"<User id={self.id} email={self.email!r}>"
	
	extra_properties = ("full_name", "is_admin", "is_trekker", "is_trek_staff")



class Trek(db.Model, TimestampMixin, ExportMixin):
	__tablename__ = "treks"

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(160), nullable=False)
	description = db.Column(db.Text, nullable=True)
	start_date = db.Column(db.Date, nullable=False)
	end_date = db.Column(db.Date, nullable=False)
	capacity = db.Column(db.Integer, nullable=False, default=1, server_default="1")
	price = db.Column(db.Numeric(10, 2), nullable=False, default=0, server_default="0")
	status = db.Column(
		db.Enum(
			TrekStatus,
			name="trek_status",
			native_enum=False,
			create_constraint=True,
			validate_strings=True,
			values_callable=enum_values,
		),
		nullable=False,
		default=TrekStatus.DRAFT,
		server_default=TrekStatus.DRAFT.value,
	)

	location = db.Column(db.String(120), nullable=False)
	staff_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
	bookings = db.relationship(
		"Booking",
		back_populates="trek",
		cascade="all, delete-orphan",
		lazy="selectin",
	)
	staff = db.relationship("User",
						foreign_keys=[staff_user_id],
						  lazy="joined")

	__table_args__ = (
		db.CheckConstraint("end_date >= start_date", name="ck_treks_date_window"),
		db.CheckConstraint("capacity > 0", name="ck_treks_capacity_positive"),
		db.CheckConstraint("price >= 0", name="ck_treks_price_non_negative"),
		db.Index("ix_treks_status_start_date", "status", "start_date"),
		db.UniqueConstraint("title", "start_date", "location", name="uq_treks_title_start_location"),
	)

	@property
	def seats_booked(self) -> int:
		return sum(1 for b in self.bookings if b.status == BookingStatus.BOOKED)
	
	@property
	def seats_available(self) -> int:
		return max(self.capacity - self.seats_booked, 0)

	@property
	def is_draft(self) -> bool:
		return self.status == TrekStatus.DRAFT
	
	@property
	def is_open(self) -> bool:
		return self.status == TrekStatus.OPEN


	@property
	def is_completed(self) -> bool:
		return self.status == TrekStatus.COMPLETED

	@property
	def is_cancelled(self) -> bool:
		return self.status == TrekStatus.CANCELLED
	
	@property
	def is_full(self) -> bool:
		return self.seats_available <= 0
	
	def open(self) -> None:
		self.status = TrekStatus.OPEN

	def complete(self) -> None:
		self.status = TrekStatus.COMPLETED

	def cancel(self) -> None:
		self.status = TrekStatus.CANCELLED

	def __repr__(self) -> str:
		return f"<Trek id={self.id} title={self.title!r} status={self.status}>"
	
	extra_properties = ("seats_booked", "seats_available", "is_draft", "is_open", "is_completed", "is_cancelled", "is_full")


class Booking(db.Model, TimestampMixin, ExportMixin):
	__tablename__ = "bookings"

	id = db.Column(db.Integer, primary_key=True)
	trek_id = db.Column(db.Integer, db.ForeignKey("treks.id", ondelete="CASCADE"), nullable=False)
	trekker_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
	price_at_booking = db.Column(db.Numeric(10, 2), nullable=False)
	status = db.Column(
		db.Enum(
			BookingStatus,
			name="booking_status",
			native_enum=False,
			create_constraint=True,
			validate_strings=True,
			values_callable=enum_values,
		),
		nullable=False,
		default=BookingStatus.BOOKED,
		server_default=BookingStatus.BOOKED.value,
	)
	notes = db.Column(db.Text, nullable=True)

	trek = db.relationship("Trek", back_populates="bookings", lazy="joined")
	trekker = db.relationship("User", back_populates="bookings", foreign_keys=[trekker_user_id], lazy="joined")

	__table_args__ = (
		db.CheckConstraint("price_at_booking >= 0", name="ck_bookings_price_non_negative"),
		db.UniqueConstraint("trek_id", "trekker_user_id", name="uq_booking_per_user_per_trek"),
		db.Index("ix_bookings_trek_id", "trek_id"),
		db.Index("ix_bookings_trekker_user_id", "trekker_user_id"),
		db.Index("ix_bookings_status_created", "status", "created_at"),
	)

	@property
	def is_booked(self) -> bool:
		return self.status == BookingStatus.BOOKED

	def cancel(self) -> None:
		self.status = BookingStatus.CANCELLED
	
	def confirm(self) -> None:
		self.status = BookingStatus.BOOKED
	
	def __repr__(self) -> str:
		return f"<Booking id={self.id} trek_id={self.trek_id} trekker_user_id={self.trekker_user_id} status={self.status}>"
	
	extra_properties = ("is_booked",)


__all__ = [
	"Booking",
	"Trek",
	"User",
]
