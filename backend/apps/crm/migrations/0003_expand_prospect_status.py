# =============================================================================
# === backend/apps/crm/migrations/0003_expand_prospect_status.py ===
# Sprint 5 (CRM Foundation Phase B): Prospect.Status expansion.
#
# Hand-written rather than machine-generated via makemigrations, since
# this needs a RunPython data step makemigrations can't produce on its
# own. Dependency is 0002_activity — confirmed directly from Chris's
# own `makemigrations` output when Sprint 4 shipped, not guessed.
#
# Reversible: migrate_backward() exists so `migrate crm 0002` cleanly
# un-does this if it's ever needed, same discipline as every other
# data migration in this codebase.
# =============================================================================
from django.db import migrations, models


def migrate_forward(apps, schema_editor):
    Prospect = apps.get_model("crm", "Prospect")
    # follow_up needs no entry here — its stored value is unchanged
    # by the Sprint 5 enum expansion, only these three actually moved.
    mapping = {"baru": "lead", "konversi": "won", "hilang": "lost"}
    for old_value, new_value in mapping.items():
        Prospect.objects.filter(status=old_value).update(status=new_value)


def migrate_backward(apps, schema_editor):
    Prospect = apps.get_model("crm", "Prospect")
    mapping = {"lead": "baru", "won": "konversi", "lost": "hilang"}
    for old_value, new_value in mapping.items():
        Prospect.objects.filter(status=old_value).update(status=new_value)


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0002_activity"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prospect",
            name="status",
            field=models.CharField(
                choices=[
                    ("lead", "Lead"),
                    ("qualified", "Qualified"),
                    ("follow_up", "Follow Up"),
                    ("site_visit", "Site Visit"),
                    ("negotiation", "Negotiation"),
                    ("won", "Won"),
                    ("lost", "Lost"),
                ],
                default="lead",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
