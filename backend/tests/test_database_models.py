import pytest
import asyncio
from datetime import datetime
from app.core.database import AsyncSessionLocal, init_db
from app.infrastructure.db.models.auth_models import HospitalModel, UserModel, RoleModel, SessionModel
from app.infrastructure.db.models.hospital import PatientModel
from app.infrastructure.db.models.claim import ClaimModel, DocumentModel, JobModel
from sqlalchemy import select

def test_database_schema_initialization_and_crud():
    async def run():
        await init_db()
        async with AsyncSessionLocal() as session:
            # 1. Create Hospital
            hosp = HospitalModel(
                name="Test Metro Hospital",
                facility_type="Inpatient Hospital",
                npi_number="1234567890"
            )
            session.add(hosp)
            await session.commit()
            await session.refresh(hosp)
            assert hosp.id is not None
            assert hosp.name == "Test Metro Hospital"

            # 2. Create User linked to Hospital
            user = UserModel(
                hospital_id=hosp.id,
                email=f"doctor_{int(datetime.now().timestamp())}@metro.org",
                hashed_password="hashed_pass_secure",
                full_name="Dr. Test User"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            assert user.hospital_id == hosp.id

            # 3. Create Patient with soft delete fields
            patient = PatientModel(
                tenant_id="tenant_default",
                hospital_id=hosp.id,
                first_name="John",
                last_name="Doe",
                medical_record_number=f"MRN-{int(datetime.now().timestamp())}"
            )
            session.add(patient)
            await session.commit()
            await session.refresh(patient)
            assert patient.is_deleted is False

            # 4. Create Claim with hospital isolation
            claim = ClaimModel(
                tenant_id="tenant_default",
                hospital_id=hosp.id,
                patient_id=patient.id,
                external_claim_ref=f"CLM-{int(datetime.now().timestamp())}",
                amount=5000.0,
                raw_payload={"diagnosis": "Appendicitis"}
            )
            session.add(claim)
            await session.commit()
            await session.refresh(claim)
            assert claim.status == "INGESTED"

            # Query verification
            result = await session.execute(select(ClaimModel).where(ClaimModel.hospital_id == hosp.id))
            claims = result.scalars().all()
            assert len(claims) >= 1

    asyncio.run(run())
