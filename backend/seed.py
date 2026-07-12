from __future__ import annotations

import argparse
import os
import random
from datetime import date, timedelta

from argon2 import PasswordHasher
from faker import Faker
from sqlalchemy import MetaData, Table, func, insert, select
from sqlalchemy.orm import Session

from application import create_app, db


def random_trek_status(rng: random.Random) -> str:
    statuses = ["draft", "open", "completed", "cancelled"]
    weights = [0.2, 0.5, 0.2, 0.1]
    return rng.choices(statuses, weights=weights, k=1)[0]


def random_booking_status(rng: random.Random) -> str:
    statuses = ["booked", "cancelled"]
    weights = [0.85, 0.15]
    return rng.choices(statuses, weights=weights, k=1)[0]


def seed_users(
    session: Session,
    users: Table,
    faker: Faker,
    ph: PasswordHasher,
    target_trekkers: int,
    target_staff: int,
) -> tuple[list[int], list[int], int]:
    admin_id = session.execute(
        select(users.c.id).where(users.c.role == "admin").limit(1)
    ).scalar_one_or_none()

    if admin_id is None:
        admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@trek.local")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "Admin@123")
        result = session.execute(
            insert(users).values(
                email=admin_email,
                password_hash=ph.hash(admin_password),
                first_name="System",
                last_name="Admin",
                role="admin",
                is_active=True,
            )
        )
        admin_id = int(result.inserted_primary_key[0])

    staff_count = session.execute(
        select(func.count()).select_from(users).where(users.c.role == "trek_staff")
    ).scalar_one()

    staff_to_create = max(target_staff - int(staff_count), 0)
    for _ in range(staff_to_create):
        session.execute(
            insert(users).values(
                email=faker.unique.email(),
                password_hash=ph.hash(faker.password(length=12, special_chars=True)),
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                role="trek_staff",
                is_active=True,
            )
        )

    trekker_count = session.execute(
        select(func.count()).select_from(users).where(users.c.role == "trekker")
    ).scalar_one()

    trekkers_to_create = max(target_trekkers - int(trekker_count), 0)
    for _ in range(trekkers_to_create):
        session.execute(
            insert(users).values(
                email=faker.unique.email(),
                password_hash=ph.hash(faker.password(length=12, special_chars=True)),
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                role="trekker",
                is_active=True,
            )
        )

    staff_ids = [
        int(row[0])
        for row in session.execute(select(users.c.id).where(users.c.role == "trek_staff")).all()
    ]
    trekker_ids = [
        int(row[0])
        for row in session.execute(select(users.c.id).where(users.c.role == "trekker")).all()
    ]

    return trekker_ids, staff_ids, int(admin_id)


def seed_treks(
    session: Session,
    treks: Table,
    faker: Faker,
    rng: random.Random,
    staff_ids: list[int],
    target_treks: int,
) -> list[dict]:
    existing_count = int(session.execute(select(func.count()).select_from(treks)).scalar_one())
    to_create = max(target_treks - existing_count, 0)

    for idx in range(to_create):
        start = date.today() + timedelta(days=rng.randint(7, 240))
        end = start + timedelta(days=rng.randint(2, 12))
        title = f"{faker.word().title()} Trail {faker.unique.bothify(text='##??')}"
        location = f"{faker.city()}, {faker.country()}"

        session.execute(
            insert(treks).values(
                title=title,
                description=faker.paragraph(nb_sentences=4),
                start_date=start,
                end_date=end,
                capacity=rng.randint(8, 40),
                price=round(rng.uniform(1200, 15000), 2),
                status=random_trek_status(rng),
                location=location,
                staff_user_id=rng.choice(staff_ids) if staff_ids else None,
            )
        )

    rows = session.execute(select(treks.c.id, treks.c.price)).all()
    return [{"id": int(r[0]), "price": r[1]} for r in rows]


def seed_bookings(
    session: Session,
    bookings: Table,
    faker: Faker,
    rng: random.Random,
    trekker_ids: list[int],
    trek_rows: list[dict],
    target_bookings: int,
) -> int:
    existing_pairs = {
        (int(row[0]), int(row[1]))
        for row in session.execute(select(bookings.c.trek_id, bookings.c.trekker_user_id)).all()
    }
    existing_count = len(existing_pairs)
    to_create = max(target_bookings - existing_count, 0)

    if not trekker_ids or not trek_rows:
        return 0

    all_pairs = [(trek["id"], user_id) for trek in trek_rows for user_id in trekker_ids]
    available_pairs = [pair for pair in all_pairs if pair not in existing_pairs]

    if to_create > len(available_pairs):
        to_create = len(available_pairs)

    selected_pairs = rng.sample(available_pairs, k=to_create) if to_create else []

    price_by_trek = {int(t["id"]): t["price"] for t in trek_rows}

    for trek_id, trekker_id in selected_pairs:
        base_price = float(price_by_trek[trek_id])
        variation = round(rng.uniform(-0.1, 0.15) * base_price, 2)
        final_price = max(round(base_price + variation, 2), 0)

        session.execute(
            insert(bookings).values(
                trek_id=trek_id,
                trekker_user_id=trekker_id,
                price_at_booking=final_price,
                status=random_booking_status(rng),
                notes=faker.sentence(nb_words=8) if rng.random() < 0.4 else None,
            )
        )

    return to_create


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed database with realistic fake data.")
    parser.add_argument("--env", type=str, default=None, help="Path to .env file")
    parser.add_argument("--trekkers", type=int, default=100, help="Target total number of trekkers")
    parser.add_argument("--staff", type=int, default=10, help="Target total number of trek staff users")
    parser.add_argument("--treks", type=int, default=20, help="Target total number of treks")
    parser.add_argument("--bookings", type=int, default=400, help="Target total number of bookings")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    app = create_app()

    with app.app_context():
        engine = db.engine
        metadata = MetaData()
        metadata.reflect(bind=engine, only=["users", "treks", "bookings"])

        users = metadata.tables.get("users")
        treks = metadata.tables.get("treks")
        bookings = metadata.tables.get("bookings")

        if users is None or treks is None or bookings is None:
            raise RuntimeError(
                "Required tables not found. Ensure users, treks, and bookings tables exist before seeding."
            )

        faker = Faker()
        faker.seed_instance(args.seed)
        rng = random.Random(args.seed)
        ph = PasswordHasher()

        with Session(engine) as session:
            trekker_ids, staff_ids, admin_id = seed_users(
                session=session,
                users=users,
                faker=faker,
                ph=ph,
                target_trekkers=args.trekkers,
                target_staff=args.staff,
            )
            trek_rows = seed_treks(
                session=session,
                treks=treks,
                faker=faker,
                rng=rng,
                staff_ids=staff_ids,
                target_treks=args.treks,
            )
            new_booking_count = seed_bookings(
                session=session,
                bookings=bookings,
                faker=faker,
                rng=rng,
                trekker_ids=trekker_ids,
                trek_rows=trek_rows,
                target_bookings=args.bookings,
            )

            session.commit()

            user_total = int(session.execute(select(func.count()).select_from(users)).scalar_one())
            staff_total = int(
                session.execute(select(func.count()).select_from(users).where(users.c.role == "trek_staff")).scalar_one()
            )
            trekker_total = int(
                session.execute(select(func.count()).select_from(users).where(users.c.role == "trekker")).scalar_one()
            )
            trek_total = int(session.execute(select(func.count()).select_from(treks)).scalar_one())
            booking_total = int(session.execute(select(func.count()).select_from(bookings)).scalar_one())

        database_url = app.config["SQLALCHEMY_DATABASE_URI"]

    print("Seeding complete")
    print(f"  database_url: {database_url}")
    print(f"  admin_user_id: {admin_id}")
    print(f"  users_total: {user_total} (trekkers={trekker_total}, staff={staff_total})")
    print(f"  treks_total: {trek_total}")
    print(f"  bookings_total: {booking_total} (new={new_booking_count})")


if __name__ == "__main__":
    main()
