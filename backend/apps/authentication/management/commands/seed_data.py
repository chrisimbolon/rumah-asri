"""
DevelopIndo — Seed Database Command
Populates the database with realistic test data for development

Usage:
  python manage.py seed_data
  python manage.py seed_data --clear   ← clears existing data first
"""

from datetime import date

from apps.authentication.models import CustomUser
from apps.construction.models import ConstructionPhase
from apps.documents.models import Document
from apps.organizations.models import Organization, OrganizationMembership
from apps.payments.models import Payment
from apps.projects.models import Project, ProjectRequirementStatus, StageRequirement
from apps.units.models import Unit
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed database with realistic DevelopIndo test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("🗑️  Clearing existing data...")
            Document.objects.all().delete()
            Payment.objects.all().delete()
            ConstructionPhase.objects.all().delete()
            Unit.objects.all().delete()
            ProjectRequirementStatus.objects.all().delete()
            Project.objects.all().delete()
            CustomUser.objects.filter(role__in=["developer", "buyer", "agent"]).delete()
            Organization.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✅ Cleared!"))

        self.stdout.write("🌱 Seeding DevelopIndo database...")

        # ── 1. Developer ───────────────────────────────────────
        developer, created = CustomUser.objects.get_or_create(
            email="developer@asrisentosa.co.id",
            defaults={
                "full_name": "Budi Developer",
                "phone":     "+62 741 555 1234",
                "role":      "developer",
                "is_active": True,
            }
        )
        if created:
            developer.set_password("DevelopIndo2026!")
            developer.save()
        self.stdout.write(f"  ✅ Developer: {developer.email}")

        # ── 1b. Organization ───────────────────────────────────
        org, org_created = Organization.objects.get_or_create(
            name="PT Asri Sentosa Properti",
        )
        OrganizationMembership.objects.get_or_create(
            organization=org, user=developer, defaults={"role": "owner"},
        )
        self.stdout.write(
            f"  ✅ Organization: {org.name} "
            f"({'created' if org_created else 'existing'})"
        )

        # ── 2. Buyers ──────────────────────────────────────────
        buyers_data = [
            {"email": "budi@gmail.com",   "full_name": "Budi Santoso",   "phone": "+62 812 3456 7890"},
            {"email": "rina@gmail.com",   "full_name": "Rina Wulandari", "phone": "+62 813 5678 9012"},
            {"email": "ahmad@gmail.com",  "full_name": "Ahmad Fauzi",    "phone": "+62 878 9012 3456"},
            {"email": "siti@gmail.com",   "full_name": "Siti Marlina",   "phone": "+62 857 3456 7890"},
            {"email": "hendra@gmail.com", "full_name": "Hendra Gunawan", "phone": "+62 811 2345 6789"},
        ]
        buyers = []
        for b in buyers_data:
            buyer, created = CustomUser.objects.get_or_create(
                email=b["email"],
                defaults={**b, "role": "buyer", "is_active": True}
            )
            if created:
                buyer.set_password("Pembeli2026!")
                buyer.save()
            buyers.append(buyer)
            self.stdout.write(f"  ✅ Buyer: {buyer.email}")

        # ── 3. Projects ────────────────────────────────────────
        projects_data = [
            {
                "name":         "Perumahan Asri Cluster A",
                "location":     "Telanaipura, Jambi",
                "description":  "Cluster premium dengan konsep modern minimalis di jantung kota Jambi.",
                "stage":        Project.Stage.CONSTRUCTION,
                "total_units":  40,
                "target_budget": 15000000000,
                "start_date":   date(2025, 1, 15),
                "end_date":     date(2025, 12, 31),
                "ipr_status":   Project.PermitStatus.APPROVED,
                "ipr_date":     date(2024, 10, 1),
                "amdal_status": Project.PermitStatus.APPROVED,
                "amdal_date":   date(2024, 11, 1),
                "pbg_status":   Project.PermitStatus.APPROVED,
                "pbg_date":     date(2025, 1, 10),
                # Intelligence snapshot — reflects completed requirements
                "readiness_score_last": 50,
            },
            {
                "name":         "Perumahan Asri Cluster B",
                "location":     "Alam Barajo, Jambi",
                "description":  "Hunian asri di kawasan hijau dengan konsep eco-living.",
                "stage":        Project.Stage.CONSTRUCTION,
                "total_units":  38,
                "target_budget": 14000000000,
                "start_date":   date(2025, 3, 1),
                "end_date":     date(2026, 2, 28),
                "ipr_status":   Project.PermitStatus.APPROVED,
                "ipr_date":     date(2024, 11, 15),
                "amdal_status": Project.PermitStatus.APPROVED,
                "amdal_date":   date(2024, 12, 1),
                "pbg_status":   Project.PermitStatus.APPROVED,
                "pbg_date":     date(2025, 2, 20),
                "readiness_score_last": 100,
            },
            {
                "name":         "Perumahan Asri Cluster C",
                "location":     "Kotabaru, Jambi",
                "description":  "Kawasan perumahan strategis dekat Jembatan Batanghari.",
                "stage":        Project.Stage.CONSTRUCTION,
                "total_units":  44,
                "target_budget": 16000000000,
                "start_date":   date(2025, 6, 1),
                "end_date":     date(2026, 5, 31),
                "ipr_status":   Project.PermitStatus.APPROVED,
                "ipr_date":     date(2025, 1, 10),
                "amdal_status": Project.PermitStatus.APPROVED,
                "amdal_date":   date(2025, 2, 15),
                "pbg_status":   Project.PermitStatus.APPROVED,
                "pbg_date":     date(2025, 5, 20),
                "readiness_score_last": 0,
            },
        ]
        projects = []
        for p in projects_data:
            project, created = Project.objects.get_or_create(
                name=p["name"],
                organization=org,
                defaults=p,
            )
            projects.append(project)
            self.stdout.write(f"  ✅ Project: {project.name} (stage: {project.stage})")

        # ── 4. Stage requirement statuses ──────────────────────
        # Auto-create ProjectRequirementStatus rows for each project
        # Then seed realistic completion states for the demo:
        #   Cluster A — 50% done (1/2 mandatory complete)
        #   Cluster B — 100% done (both mandatory complete, can advance)
        #   Cluster C — 0% done (nothing started)
        from django.utils import timezone

        for project in projects:
            project._create_stage_requirements()

        self.stdout.write("  ✅ Stage requirement statuses created")

        # Cluster A — "Rencana kerja" completed, "Kontraktor" pending
        cluster_a = projects[0]
        req_rencana = StageRequirement.objects.filter(
            stage=Project.Stage.CONSTRUCTION, name="Rencana kerja"
        ).first()
        if req_rencana:
            status_obj = ProjectRequirementStatus.objects.filter(
                project=cluster_a, requirement=req_rencana
            ).first()
            if status_obj:
                status_obj.status       = ProjectRequirementStatus.Status.COMPLETED
                status_obj.completed_at = timezone.now()
                status_obj.updated_by   = developer
                status_obj.save()
                self.stdout.write("  ✅ Cluster A: Rencana kerja → selesai (50% readiness)")

        # Cluster B — both mandatory requirements completed (can advance!)
        cluster_b = projects[1]
        for req_name in ["Rencana kerja", "Kontraktor"]:
            req = StageRequirement.objects.filter(
                stage=Project.Stage.CONSTRUCTION, name=req_name
            ).first()
            if req:
                status_obj = ProjectRequirementStatus.objects.filter(
                    project=cluster_b, requirement=req
                ).first()
                if status_obj:
                    status_obj.status       = ProjectRequirementStatus.Status.COMPLETED
                    status_obj.completed_at = timezone.now()
                    status_obj.updated_by   = developer
                    status_obj.save()
        self.stdout.write("  ✅ Cluster B: Rencana kerja + Kontraktor → selesai (100% readiness, siap maju)")

        # Cluster C — nothing done (0% readiness, shows "Risiko Sedang")
        self.stdout.write("  ✅ Cluster C: Belum ada requirement selesai (0% readiness)")

        # ── 5. Units ───────────────────────────────────────────
        units_data = [
            {
                "project":           projects[0],
                "buyer":             buyers[0],
                "unit_number":       "A-01",
                "unit_type":         "Tipe 45",
                "land_area":         72,
                "building_area":     45,
                "price":             850000000,
                "status":            "proses",
                "progress":          85,
                "current_phase":     "Finishing interior",
                "target_completion": date(2025, 8, 31),
                "payment_method":    "KPR BCA",
                "bank":              "BCA",
            },
            {
                "project":           projects[0],
                "buyer":             buyers[3],
                "unit_number":       "A-05",
                "unit_type":         "Tipe 45",
                "land_area":         72,
                "building_area":     45,
                "price":             850000000,
                "status":            "proses",
                "progress":          22,
                "current_phase":     "Pembersihan lahan selesai",
                "target_completion": date(2025, 11, 30),
                "payment_method":    "KPR Mandiri",
                "bank":              "Mandiri",
            },
            {
                "project":           projects[1],
                "buyer":             buyers[1],
                "unit_number":       "B-07",
                "unit_type":         "Tipe 54",
                "land_area":         90,
                "building_area":     54,
                "price":             920000000,
                "status":            "terjual",
                "progress":          68,
                "current_phase":     "Dinding struktural",
                "target_completion": date(2025, 9, 30),
                "payment_method":    "KPR BNI",
                "bank":              "BNI",
            },
            {
                "project":           projects[2],
                "buyer":             buyers[2],
                "unit_number":       "C-03",
                "unit_type":         "Tipe 36",
                "land_area":         60,
                "building_area":     36,
                "price":             780000000,
                "status":            "proses",
                "progress":          42,
                "current_phase":     "Pondasi selesai",
                "target_completion": date(2025, 10, 31),
                "payment_method":    "Cash bertahap",
                "bank":              "",
            },
            {
                "project":           projects[2],
                "buyer":             buyers[4],
                "unit_number":       "C-15",
                "unit_type":         "Tipe 45",
                "land_area":         72,
                "building_area":     45,
                "price":             780000000,
                "status":            "tersedia",
                "progress":          0,
                "current_phase":     "",
                "target_completion": None,
                "payment_method":    "",
                "bank":              "",
            },
        ]
        units = []
        for u in units_data:
            unit, created = Unit.objects.get_or_create(
                project=u["project"],
                unit_number=u["unit_number"],
                defaults=u,
            )
            units.append(unit)
            self.stdout.write(f"  ✅ Unit: {unit.unit_number} ({unit.project.name})")

        # ── 6. Construction Phases for Unit A-01 ──────────────
        phases_data = [
            {"phase_order": 1, "phase_name": "Pembersihan & persiapan lahan",   "phase_date": "Jan 2025",     "status": "selesai", "notes": "Lahan dibersihkan & diratakan. Uji tanah lulus."},
            {"phase_order": 2, "phase_name": "Pekerjaan pondasi",               "phase_date": "Feb 2025",     "status": "selesai", "notes": "Pondasi beton dituang. 3 foto lapangan diunggah."},
            {"phase_order": 3, "phase_name": "Rangka struktur",                 "phase_date": "Apr 2025",     "status": "selesai", "notes": "Rangka baja & kolom selesai dikerjakan."},
            {"phase_order": 4, "phase_name": "Dinding struktural",              "phase_date": "Mei 2025",     "status": "selesai", "notes": "Pasangan bata & plesteran selesai."},
            {"phase_order": 5, "phase_name": "Pemasangan atap & waterproofing", "phase_date": "Jun 2025",     "status": "selesai", "notes": "Genteng dipasang, waterproofing atap selesai."},
            {"phase_order": 6, "phase_name": "Finishing interior",              "phase_date": "Jul–Agu 2025", "status": "proses",  "notes": "Pengecatan lantai bawah selesai. Keramik sedang berjalan."},
            {"phase_order": 7, "phase_name": "Selesai / serah terima",         "phase_date": "Sep 2025",     "status": "menunggu","notes": ""},
        ]
        unit_a01 = units[0]
        for ph in phases_data:
            ConstructionPhase.objects.get_or_create(
                unit=unit_a01,
                phase_order=ph["phase_order"],
                defaults={**ph, "updated_by": developer},
            )
        self.stdout.write("  ✅ Construction phases for Unit A-01 (7 phases)")

        # ── 7. Payments for Unit A-01 ──────────────────────────
        payments_data = [
            {"payment_type": "Cicilan KPR #8",  "due_date": date(2026, 3, 1), "amount": 7200000, "status": "lunas",       "bank": "BCA"},
            {"payment_type": "Cicilan KPR #9",  "due_date": date(2026, 4, 1), "amount": 7200000, "status": "akan_datang", "bank": "BCA"},
            {"payment_type": "Cicilan KPR #10", "due_date": date(2026, 5, 1), "amount": 7200000, "status": "akan_datang", "bank": "BCA"},
        ]
        for p in payments_data:
            Payment.objects.get_or_create(
                unit=unit_a01,
                payment_type=p["payment_type"],
                defaults=p,
            )
        self.stdout.write("  ✅ Payments for Unit A-01 (3 records)")

        # ── 8. Documents for Unit A-01 ─────────────────────────
        documents_data = [
            {"doc_type": "ppjb",     "name": "PPJB — Perjanjian Pengikatan Jual Beli", "status": "tersedia", "issued_date": "Jan 2025"},
            {"doc_type": "imb",      "name": "IMB — Izin Mendirikan Bangunan",          "status": "tersedia", "issued_date": "Des 2024"},
            {"doc_type": "ajb",      "name": "Sertifikat Tanah (AJB)",                  "status": "proses",   "issued_date": "Proses KPR"},
            {"doc_type": "invoice",  "name": "Faktur Pajak PPN",                        "status": "tersedia", "issued_date": "Jan 2025"},
            {"doc_type": "handover", "name": "Berita Acara Serah Terima",               "status": "menunggu", "issued_date": "Sep 2025"},
        ]
        for d in documents_data:
            Document.objects.get_or_create(
                unit=unit_a01,
                doc_type=d["doc_type"],
                defaults={**d, "uploaded_by": developer},
            )
        self.stdout.write("  ✅ Documents for Unit A-01 (5 documents)")

        # ── Done ───────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("🎉 Database seeded successfully!!"))
        self.stdout.write("")
        self.stdout.write("📊 Intelligence state:")
        self.stdout.write("  Cluster A: 50% readiness  — 1 blocking  — Risk: Sedang  — Trend: ↘ Declining")
        self.stdout.write("  Cluster B: 100% readiness — 0 blocking  — Risk: Rendah  — Trend: ↗ Improving")
        self.stdout.write("  Cluster C: 0% readiness   — 2 blocking  — Risk: Sedang  — Trend: → Stable")
        self.stdout.write("")
        self.stdout.write("📋 Test accounts:")
        self.stdout.write("  Developer: developer@asrisentosa.co.id / DevelopIndo2026!")
        self.stdout.write("  Buyer:     budi@gmail.com / Pembeli2026!")
        self.stdout.write("")
        self.stdout.write("🔗 API endpoints ready:")
        self.stdout.write("  GET  /api/projects/portfolio/              ← Intelligence overview")
        self.stdout.write("  GET  /api/projects/<id>/intelligence/      ← Full intelligence")
        self.stdout.write("  PUT  /api/projects/<id>/requirements/<id>/ ← Update requirement")
        self.stdout.write("  POST /api/projects/<id>/advance/           ← Advance stage")
