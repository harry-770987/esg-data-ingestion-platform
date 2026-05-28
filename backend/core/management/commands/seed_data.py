import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Tenant, DataSource

class Command(BaseCommand):
    help = "Seeds the database with initial Tenants, DataSources, and a standard auditor user."

    def handle(self, *args, **options):
        self.stdout.write("Seeding database data...")

        # 1. Create a default Auditor User
        user, created = User.objects.get_or_create(username="auditor")
        if created:
            user.set_password("password123")
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS("Created admin auditor user 'auditor' with password 'password123'."))
        else:
            self.stdout.write("User 'auditor' already exists.")

        # 2. Seed Tenant Alpha Corp
        tenant_a_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        tenant_a, created = Tenant.objects.get_or_create(
            id=tenant_a_id,
            defaults={"name": "Alpha Corporate Client"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Tenant Alpha Corp: {tenant_a.id}"))
        else:
            self.stdout.write(f"Tenant Alpha Corp already exists: {tenant_a.id}")

        # 3. Seed Tenant Beta Corp
        tenant_b_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        tenant_b, created = Tenant.objects.get_or_create(
            id=tenant_b_id,
            defaults={"name": "Beta Industries Group"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Tenant Beta Corp: {tenant_b.id}"))
        else:
            self.stdout.write(f"Tenant Beta Corp already exists: {tenant_b.id}")

        # 4. Seed standard DataSources for Tenant Alpha
        sources = [
            ("SAP Fuel Log", "SAP_FUEL", "Fuel procurement lines"),
            ("Grid Electricity Meter", "UTILITY_ELEC", "Utility company invoice files"),
            ("Expedia Business Travel", "TRAVEL_CORP", "Corporate travel platform exports")
        ]

        for name, source_type, desc in sources:
            ds, created = DataSource.objects.get_or_create(
                tenant=tenant_a,
                source_type=source_type,
                defaults={"name": name, "description": desc, "is_active": True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created DataSource for Tenant Alpha: {name} ({source_type})"))

        # 5. Seed standard DataSources for Tenant Beta
        for name, source_type, desc in sources:
            ds, created = DataSource.objects.get_or_create(
                tenant=tenant_b,
                source_type=source_type,
                defaults={"name": name, "description": desc, "is_active": True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created DataSource for Tenant Beta: {name} ({source_type})"))

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
