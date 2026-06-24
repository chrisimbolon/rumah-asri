# =============================================================================
# === backend/apps/projects/management/commands/seed_stage_requirements.py ===
# =============================================================================
"""
DevelopIndo — Seed Stage Requirements

Seeds the default Perumahan (Township) requirements for each lifecycle stage.
Based on co-founder's visualization: "Stage Templates — Perumahan (Township)"

Usage:
  python manage.py seed_stage_requirements
  python manage.py seed_stage_requirements --clear
"""
from django.core.management.base import BaseCommand

from apps.projects.models import StageRequirement


# Default requirements per stage — Perumahan/Township template
# is_mandatory=True  → blocks stage advancement
# is_mandatory=False → shown as checklist but doesn't block
REQUIREMENTS = {
    "draft": [
        {"name": "Nama proyek",    "description": "Nama resmi proyek properti",                     "is_mandatory": True,  "order": 1},
        {"name": "Lokasi proyek",  "description": "Alamat atau area proyek",                         "is_mandatory": True,  "order": 2},
        {"name": "Deskripsi",      "description": "Gambaran umum dan konsep proyek",                 "is_mandatory": False, "order": 3},
    ],
    "perencanaan": [
        {"name": "Site plan",      "description": "Peta kavling dan tata letak unit",                "is_mandatory": True,  "order": 1},
        {"name": "Masterplan",     "description": "Rencana induk kawasan perumahan",                 "is_mandatory": True,  "order": 2},
        {"name": "RAB",            "description": "Rencana Anggaran Biaya proyek",                   "is_mandatory": True,  "order": 3},
        {"name": "Inventory unit", "description": "Daftar unit: blok, tipe, luas tanah & bangunan", "is_mandatory": True,  "order": 4},
        {"name": "Tanggal mulai",  "description": "Tanggal dimulainya proyek",                       "is_mandatory": False, "order": 5},
        {"name": "Target selesai", "description": "Target tanggal penyelesaian proyek",              "is_mandatory": False, "order": 6},
    ],
    "perizinan": [
        {"name": "IPR disetujui",   "description": "Izin Pemanfaatan Ruang dari pemerintah daerah",  "is_mandatory": True,  "order": 1},
        {"name": "AMDAL disetujui", "description": "Analisis Mengenai Dampak Lingkungan",            "is_mandatory": True,  "order": 2},
        {"name": "PBG diterbitkan", "description": "Persetujuan Bangunan Gedung — WAJIB sebelum konstruksi", "is_mandatory": True, "order": 3},
    ],
    "konstruksi": [
        {"name": "Rencana kerja",   "description": "Jadwal dan rencana pelaksanaan konstruksi",      "is_mandatory": True,  "order": 1},
        {"name": "Kontraktor",      "description": "Kontraktor utama ditunjuk dan kontrak ditandatangani", "is_mandatory": True, "order": 2},
        {"name": "Jadwal proyek",   "description": "Milestone pembangunan per unit/cluster",         "is_mandatory": False, "order": 3},
        {"name": "Progress update", "description": "Update progress konstruksi rutin",               "is_mandatory": False, "order": 4},
    ],
    "penjualan": [
        {"name": "Marketing plan",  "description": "Rencana pemasaran dan strategi penjualan",       "is_mandatory": True,  "order": 1},
        {"name": "Price list",      "description": "Daftar harga unit yang sudah ditetapkan",        "is_mandatory": True,  "order": 2},
        {"name": "Sales team",      "description": "Tim penjualan dan agen siap bertugas",           "is_mandatory": False, "order": 3},
        {"name": "Brosur & materi", "description": "Materi marketing siap didistribusikan",          "is_mandatory": False, "order": 4},
    ],
    "serah_terima": [
        {"name": "BA serah terima", "description": "Berita Acara Serah Terima per unit",             "is_mandatory": True,  "order": 1},
        {"name": "AJB",             "description": "Akta Jual Beli semua unit terjual",              "is_mandatory": True,  "order": 2},
        {"name": "Dokumentasi",     "description": "Dokumentasi lengkap serah terima",               "is_mandatory": False, "order": 3},
    ],
    "selesai": [
        {"name": "Laporan akhir",   "description": "Laporan penyelesaian proyek",                    "is_mandatory": True,  "order": 1},
        {"name": "Rekonsiliasi",    "description": "Rekonsiliasi keuangan proyek",                   "is_mandatory": False, "order": 2},
    ],
}


class Command(BaseCommand):
    help = "Seed default stage requirements (Perumahan/Township template)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing requirements before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count = StageRequirement.objects.all().delete()[0]
            self.stdout.write(f"🗑️  Cleared {count} existing requirements")

        self.stdout.write("🌱 Seeding stage requirements...")
        total_created = 0
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
                    },
                )
                flag = "✅ Created" if created else "  → Exists"
                mandatory = "⚡ wajib" if obj.is_mandatory else "○ opsional"
                self.stdout.write(f"  {flag}: [{stage}] {obj.name} ({mandatory})")
                if created:
                    total_created += 1
                else:
                    total_existing += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"🎉 Done! {total_created} created, {total_existing} already existed"
        ))
        self.stdout.write("")
        self.stdout.write("📋 Stage requirement counts:")
        for stage, reqs in REQUIREMENTS.items():
            mandatory = sum(1 for r in reqs if r["is_mandatory"])
            self.stdout.write(
                f"  {stage}: {len(reqs)} total ({mandatory} mandatory)"
            )
