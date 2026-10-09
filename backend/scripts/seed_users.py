"""Seed default users (shopowner & customer) and initial enquiries."""
import sys
from pathlib import Path

# Add backend directory to sys.path so app imports work
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from app.database.database import SessionLocal
from app.database.models import User, Product, Enquiry
from app.utils.security import hash_password


def seed_users_and_enquiries():
    db = SessionLocal()
    try:
        # 1. Create Demo Shop Owner
        owner = db.scalar(select(User).where(User.email == "owner@lumiere.com"))
        if not owner:
            owner = User(
                email="owner@lumiere.com",
                password_hash=hash_password("owner123"),
                full_name="Lumière Master Jeweller",
                role="shopowner",
                phone="+91 98765 43210",
                is_active=True,
            )
            db.add(owner)
            print("Created default shop owner: owner@lumiere.com (password: owner123)")
        else:
            print("Shop owner already exists.")

        # 2. Create Demo Customer
        customer = db.scalar(select(User).where(User.email == "customer@example.com"))
        if not customer:
            customer = User(
                email="customer@example.com",
                password_hash=hash_password("customer123"),
                full_name="Sophia Vance",
                role="customer",
                phone="+91 91234 56789",
                is_active=True,
            )
            db.add(customer)
            print("Created default customer: customer@example.com (password: customer123)")
        else:
            print("Customer already exists.")

        db.commit()

        # 3. Seed some initial client enquiries if few exist so the shopowner has orders across statuses
        existing_enquiries_count = db.query(Enquiry).count()
        if existing_enquiries_count < 3:
            products = db.scalars(select(Product).limit(4)).all()
            if products:
                sample_enquiries = [
                    Enquiry(
                        product_id=products[1].id if len(products) > 1 else products[0].id,
                        name="Aarav Sharma",
                        email="aarav.sharma@gmail.com",
                        phone="+91 98112 34567",
                        status="contacted",
                        message=f"Can you provide a certificate of authenticity for the stones on {products[1].name if len(products) > 1 else products[0].name}? Also what is the delivery timeline to Mumbai?",
                    ),
                    Enquiry(
                        product_id=products[2].id if len(products) > 2 else products[0].id,
                        name="Meera Kapoor",
                        email="meera.k@outlook.com",
                        phone="+91 97654 32109",
                        status="completed",
                        message=f"Interested in viewing this piece in your private salon. Order confirmed after bespoke fitting.",
                    ),
                ]
                db.add_all(sample_enquiries)
                db.commit()
                print(f"Added demo enquiries for shop owner review.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_users_and_enquiries()
