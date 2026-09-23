"""Seed script to populate database with realistic enterprise certificate records."""
import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.certificate import Certificate
from app.models.renewal import RenewalRequest
from app.utils.logger import logger

CUSTOMERS = [
    "Customer A",
    "Customer B",
    "Customer C",
    "Customer D",
    "Customer E",
    "Customer F",
    "Customer G",
]

DOMAINS_BY_CUSTOMER = {
    "Customer A": ["api.customera.com", "auth.customera.com", "portal.customera.com", "pay.customera.com", "cdn.customera.com", "vpn.customera.com"],
    "Customer B": ["api.customerb.org", "legacy.customerb.org", "app.customerb.org", "sso.customerb.org", "gateway.customerb.org"],
    "Customer C": ["checkout.customerc.io", "cloud.customerc.io", "data.customerc.io", "micro.customerc.io", "connect.customerc.io"],
    "Customer D": ["finance.customerd.net", "admin.customerd.net", "services.customerd.net", "core.customerd.net"],
    "Customer E": ["ops.customere.tech", "registry.customere.tech", "metrics.customere.tech", "node.customere.tech"],
    "Customer F": ["edge.customerf.co", "stream.customerf.co", "relay.customerf.co"],
    "Customer G": ["secure.customerg.com", "vault.customerg.com", "mail.customerg.com"],
}

CERT_TYPES = ["TLS", "mTLS", "CodeSigning", "ClientAuth"]

REVOCATION_REASONS = [
    "KeyCompromise",
    "CACompromise",
    "AffiliationChanged",
    "Superseded",
    "CessationOfOperation",
]

def init_db():
    """Create all database tables."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized.")

def generate_seed_certificates() -> list:
    """Generate at least 100 realistic certificate records anchored to today."""
    today = date.today()
    certificates = []

    # 1. Mandatory specific record ABC123 (Customer A, TLS, expiring in 12 days, active)
    certificates.append(
        Certificate(
            certificate_id="ABC123",
            customer_name="Customer A",
            domain="api.customera.com",
            certificate_type="TLS",
            issued_at=today - timedelta(days=350),
            expires_at=today + timedelta(days=12),
            status="ACTIVE",
            revoked=False,
            revocation_date=None,
            revocation_reason=None,
        )
    )

    # 2. Mandatory specific record XYZ789 (Customer B, Revoked)
    certificates.append(
        Certificate(
            certificate_id="XYZ789",
            customer_name="Customer B",
            domain="legacy.customerb.org",
            certificate_type="TLS",
            issued_at=today - timedelta(days=200),
            expires_at=today + timedelta(days=165),
            status="REVOKED",
            revoked=True,
            revocation_date=today - timedelta(days=15),
            revocation_reason="KeyCompromise",
        )
    )

    # 3. Dedicated expiring certificates for the next 30 days (6 more records so total in 30 days is 7)
    expiring_soon_specs = [
        ("CERT-EXP-01", "Customer A", "auth.customera.com", "TLS", 5),
        ("CERT-EXP-02", "Customer B", "app.customerb.org", "mTLS", 10),
        ("CERT-EXP-03", "Customer C", "checkout.customerc.io", "TLS", 18),
        ("CERT-EXP-04", "Customer A", "portal.customera.com", "ClientAuth", 22),
        ("CERT-EXP-05", "Customer D", "finance.customerd.net", "TLS", 25),
        ("CERT-EXP-06", "Customer E", "ops.customere.tech", "CodeSigning", 28),
    ]

    for cert_id, cust, dom, ctype, days in expiring_soon_specs:
        certificates.append(
            Certificate(
                certificate_id=cert_id,
                customer_name=cust,
                domain=dom,
                certificate_type=ctype,
                issued_at=today - timedelta(days=340),
                expires_at=today + timedelta(days=days),
                status="ACTIVE",
                revoked=False,
            )
        )

    # 4. Next calendar month certificates (for "expiring next month" queries)
    # Calculate next calendar month range
    if today.month == 12:
        next_month_year = today.year + 1
        next_month = 1
    else:
        next_month_year = today.year
        next_month = today.month + 1

    next_month_specs = [
        ("CERT-NM-01", "Customer A", "vpn.customera.com", "TLS", date(next_month_year, next_month, 5)),
        ("CERT-NM-02", "Customer B", "gateway.customerb.org", "mTLS", date(next_month_year, next_month, 12)),
        ("CERT-NM-03", "Customer C", "cloud.customerc.io", "TLS", date(next_month_year, next_month, 19)),
        ("CERT-NM-04", "Customer D", "admin.customerd.net", "ClientAuth", date(next_month_year, next_month, 24)),
    ]
    for cert_id, cust, dom, ctype, exp_date in next_month_specs:
        certificates.append(
            Certificate(
                certificate_id=cert_id,
                customer_name=cust,
                domain=dom,
                certificate_type=ctype,
                issued_at=today - timedelta(days=300),
                expires_at=exp_date,
                status="ACTIVE",
                revoked=False,
            )
        )

    # 5. Some expired certificates (10 records)
    for i in range(1, 11):
        cust = random.choice(CUSTOMERS)
        domain = random.choice(DOMAINS_BY_CUSTOMER.get(cust, ["example.com"]))
        days_ago = random.randint(10, 180)
        certificates.append(
            Certificate(
                certificate_id=f"CERT-EXPIRED-{i:02d}",
                customer_name=cust,
                domain=f"old-{i}.{domain}",
                certificate_type=random.choice(CERT_TYPES),
                issued_at=today - timedelta(days=days_ago + 365),
                expires_at=today - timedelta(days=days_ago),
                status="EXPIRED",
                revoked=False,
            )
        )

    # 6. Additional revoked certificates (8 records)
    for i in range(1, 9):
        cust = random.choice(CUSTOMERS)
        domain = random.choice(DOMAINS_BY_CUSTOMER.get(cust, ["example.com"]))
        rev_days = random.randint(5, 60)
        certificates.append(
            Certificate(
                certificate_id=f"CERT-REVOKED-{i:02d}",
                customer_name=cust,
                domain=f"compromised-{i}.{domain}",
                certificate_type=random.choice(CERT_TYPES),
                issued_at=today - timedelta(days=120),
                expires_at=today + timedelta(days=245),
                status="REVOKED",
                revoked=True,
                revocation_date=today - timedelta(days=rev_days),
                revocation_reason=random.choice(REVOCATION_REASONS),
            )
        )

    # 7. Broad population of active certificates (expiring 45 days to 720 days out)
    current_count = len(certificates)
    target_count = 115  # comfortably above 100 records
    remaining = target_count - current_count

    for i in range(1, remaining + 1):
        cust = CUSTOMERS[(i % len(CUSTOMERS))]
        domain_list = DOMAINS_BY_CUSTOMER[cust]
        base_domain = domain_list[i % len(domain_list)]
        sub = f"sub-{i}"
        full_domain = f"{sub}.{base_domain}"
        days_ahead = random.randint(45, 600)
        ctype = CERT_TYPES[i % len(CERT_TYPES)]

        certificates.append(
            Certificate(
                certificate_id=f"CERT-{cust[:4].upper()}-{i:03d}",
                customer_name=cust,
                domain=full_domain,
                certificate_type=ctype,
                issued_at=today - timedelta(days=random.randint(30, 200)),
                expires_at=today + timedelta(days=days_ahead),
                status="ACTIVE",
                revoked=False,
            )
        )

    return certificates

def seed_database():
    """Seed the database with initial certificates and sample renewal requests."""
    init_db()
    db: Session = SessionLocal()
    try:
        existing_count = db.query(Certificate).count()
        if existing_count >= 100:
            logger.info(f"Database already seeded with {existing_count} certificates.")
            return

        # Clear existing records if any
        db.query(RenewalRequest).delete()
        db.query(Certificate).delete()
        db.commit()

        certs = generate_seed_certificates()
        db.bulk_save_objects(certs)
        db.commit()
        logger.info(f"Successfully seeded {len(certs)} certificate records.")

        # Seed one sample renewal request for a known cert (e.g. CERT-EXP-06)
        sample_renewal = RenewalRequest(
            request_id="REN-2026-0001",
            certificate_id="CERT-EXP-06",
            customer_name="Customer E",
            status="PENDING",
            requested_by="ops-agent",
        )
        db.add(sample_renewal)
        db.commit()
        logger.info("Sample renewal request REN-2026-0001 seeded.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
