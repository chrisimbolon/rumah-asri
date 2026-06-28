# =============================================================================
# === backend/apps/projects/management/commands/seed_stage_requirements.py ===
# Sprint 5: adds weight per requirement
# Weights reflect real-world importance in Indonesian PropTech
# =============================================================================
"""
DevelopIndo — Seed Stage Requirements

Sprint 5: each requirement now has a weight.
Weight reasoning:
  - perizinan: PBG is the critical blocker (w=50), IPR+AMDAL are prerequisites (w=25 each)
  - konstruksi: Rencana kerja + Kontraktor are equal critical (w=40 each)
  - penjualan: Marketing plan is the foundation (w=60), Price list enables sales (w=40)
  - perencanaan: Inventory unit is most critical (w=40), others split remaining 60
  - serah_terima: BA + AJB are equal legal documents (w=50 each)

Usage:
  python manage.py seed_stage_requirements
  python manage.py seed_stage_requirements --clear
"""
from django.core.management.base import BaseCommand

from apps.projects.models import StageRequirement


REQUIREMENTS = {
    "draft": [
        {"name": "Nama proyek",   "description": "Nama resmi proyek properti",                     "is_mandatory": True,  "order": 1, "weight": 50},
        {"name": "Lokasi proyek", "description": "Alamat atau area proyek",                         "is_mandatory": True,  "order": 2, "weight": 50},
        {"name": "Deskripsi",     "description": "Gambaran umum dan konsep proyek",                 "is_mandatory": False, "order": 3, "weight": 0 },
    ],
    "perencanaan": [
        {"name": "Site plan",      "description": "Peta kavling dan tata letak unit",                "is_mandatory": True,  "order": 1, "weight": 20},
        {"name": "Masterplan",     "description": "Rencana induk kawasan perumahan",                 "is_mandatory": True,  "order": 2, "weight": 20},
        {"name": "RAB",            "description": "Rencana Anggaran Biaya proyek",                   "is_mandatory": True,  "order": 3, "weight": 20},
        {"name": "Inventory unit", "description": "Daftar unit: blok, tipe, luas tanah & bangunan", "is_mandatory": True,  "order": 4, "weight": 40},
        {"name": "Tanggal mulai",  "description": "Tanggal dimulainya proyek",                       "is_mandatory": False, "order": 5, "weight": 0 },
        {"name": "Target selesai", "description": "Target tanggal penyelesaian proyek",              "is_mandatory": False, "order": 6, "weight": 0 },
    ],
    "perizinan": [
        # IPR → AMDAL → PBG (dependency chain)
        # PBG is the final gate — heaviest weight
        {"name": "IPR disetujui",   "description": "Izin Pemanfaatan Ruang dari pemerintah daerah",           "is_mandatory": True, "order": 1, "weight": 25},
        {"name": "AMDAL disetujui", "description": "Analisis Mengenai Dampak Lingkungan",                     "is_mandatory": True, "order": 2, "weight": 25},
        {"name": "PBG diterbitkan", "description": "Persetujuan Bangunan Gedung — WAJIB sebelum konstruksi",  "is_mandatory": True, "order": 3, "weight": 50},
    ],
    "konstruksi": [
        # Rencana kerja + Kontraktor are the two critical blockers
        # Jadwal + Progress are optional support items
        {"name": "Rencana kerja",   "description": "Jadwal dan rencana pelaksanaan konstruksi",               "is_mandatory": True,  "order": 1, "weight": 40},
        {"name": "Kontraktor",      "description": "Kontraktor utama ditunjuk dan kontrak ditandatangani",     "is_mandatory": True,  "order": 2, "weight": 60},
        {"name": "Jadwal proyek",   "description": "Milestone pembangunan per unit/cluster",                   "is_mandatory": False, "order": 3, "weight": 0 },
        {"name": "Progress update", "description": "Update progress konstruksi rutin",                         "is_mandatory": False, "order": 4, "weight": 0 },
    ],
    "penjualan": [
        # Marketing plan is the foundation strategy — heavier
        # Price list enables actual sales — critical
        {"name": "Marketing plan",  "description": "Rencana pemasaran dan strategi penjualan",                 "is_mandatory": True,  "order": 1, "weight": 60},
        {"name": "Price list",      "description": "Daftar harga unit yang sudah ditetapkan",                  "is_mandatory": True,  "order": 2, "weight": 40},
        {"name": "Sales team",      "description": "Tim penjualan dan agen siap bertugas",                     "is_mandatory": False, "order": 3, "weight": 0 },
        {"name": "Brosur & materi", "description": "Materi marketing siap didistribusikan",                    "is_mandatory": False, "order": 4, "weight": 0 },
    ],
    "serah_terima": [
        # BA serah terima + AJB are equally critical legal documents
        {"name": "BA serah terima", "description": "Berita Acara Serah Terima per unit",                       "is_mandatory": True,  "order": 1, "weight": 50},
        {"name": "AJB",             "description": "Akta Jual Beli semua unit terjual",                        "is_mandatory": True,  "order": 2, "weight": 50},
        {"name": "Dokumentasi",     "description": "Dokumentasi lengkap serah terima",                         "is_mandatory": False, "order": 3, "weight": 0 },
    ],
    "selesai": [
        {"name": "Laporan akhir",   "description": "Laporan penyelesaian proyek",                              "is_mandatory": True,  "order": 1, "weight": 100},
        {"name": "Rekonsiliasi",    "description": "Rekonsiliasi keuangan proyek",                             "is_mandatory": False, "order": 2, "weight": 0  },
    ],
}

# Sprint 4: dependency chains — unchanged
DEPENDENCIES = {
    "perizinan": [
        ("AMDAL disetujui", "IPR disetujui"),
        ("PBG diterbitkan", "IPR disetujui"),
        ("PBG diterbitkan", "AMDAL disetujui"),
    ],
    "konstruksi": [
        ("Kontraktor",    "Rencana kerja"),
        ("Jadwal proyek", "Kontraktor"),
    ],
    "penjualan": [
        ("Price list", "Marketing plan"),
    ],
}


class Command(BaseCommand):
    help = "Seed default stage requirements with weights (Sprint 5)"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing requirements before seeding")

    def handle(self, *args, **options):
        if options["clear"]:
            count = StageRequirement.objects.all().delete()[0]
            self.stdout.write(f"🗑️  Cleared {count} existing requirements")

        self.stdout.write("🌱 Seeding stage requirements with weights...")
        total_created  = 0
        total_updated  = 0
        total_existing = 0

        for stage, reqs in REQUIREMENTS.items():
            for req_data in reqs:
                obj, created = StageRequirement.objects.get_or_create(
                    stage=stage,
                    name=req_data["name"],
                    defaults={
                        "description":  req_data["description"],
                        "is_mandatory": req_data["is_mandatory"],
                        "order":        req_data["order"],
                        "is_active":    True,
                        "weight":       req_data["weight"],
                    },
                )
                if created:
                    flag = "✅ Created"
                    total_created += 1
                elif obj.weight != req_data["weight"]:
                    # Sprint 5: update weight if it changed
                    obj.weight = req_data["weight"]
                    obj.save(update_fields=["weight", "updated_at"])
                    flag = "⚡ Updated weight"
                    total_updated += 1
                else:
                    flag = "  → Exists"
                    total_existing += 1

                mandatory = "⚡ wajib" if obj.is_mandatory else "○ opsional"
                weight_str = f"w={obj.weight}" if obj.is_mandatory else "w=0"
                self.stdout.write(f"  {flag}: [{stage}] {obj.name} ({mandatory}, {weight_str})")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"🎉 Done! {total_created} created, {total_updated} weight-updated, {total_existing} unchanged"
        ))

        # ── Seed dependency chains ────────────────────────────
        self.stdout.write("")
        self.stdout.write("🔗 Seeding dependency chains...")
        dep_created = 0
        dep_skipped = 0

        for stage, deps in DEPENDENCIES.items():
            for dependent_name, prereq_name in deps:
                try:
                    dependent = StageRequirement.objects.get(stage=stage, name=dependent_name)
                    prereq    = StageRequirement.objects.get(stage=stage, name=prereq_name)
                    if prereq not in dependent.prerequisites.all():
                        dependent.prerequisites.add(prereq)
                        self.stdout.write(f"  ✅ [{stage}] {dependent_name} → requires → {prereq_name}")
                        dep_created += 1
                    else:
                        self.stdout.write(f"  → Exists: [{stage}] {dependent_name} → {prereq_name}")
                        dep_skipped += 1
                except StageRequirement.DoesNotExist as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠ Skipped: {e}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"🔗 Dependencies: {dep_created} created, {dep_skipped} already existed"
        ))

        # ── Summary ───────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write("📋 Stage weights summary:")
        for stage, reqs in REQUIREMENTS.items():
            mandatory = [r for r in reqs if r["is_mandatory"]]
            total_w   = sum(r["weight"] for r in mandatory)
            self.stdout.write(f"  {stage}: total_weight={total_w} across {len(mandatory)} mandatory")
            for r in mandatory:
                self.stdout.write(f"    {r['name']}: w={r['weight']} ({r['weight']}%)")
