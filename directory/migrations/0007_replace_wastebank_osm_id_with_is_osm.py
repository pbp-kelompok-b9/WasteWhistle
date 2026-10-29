from django.db import migrations, models


def mark_existing_osm_banks(apps, schema_editor):
    WasteBank = apps.get_model("directory", "WasteBank")
    WasteBank.objects.exclude(osm_id__isnull=True).exclude(osm_id="").update(is_osm=True)


class Migration(migrations.Migration):

    dependencies = [
        ("directory", "0006_wastebank_osm_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="wastebank",
            name="is_osm",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            mark_existing_osm_banks,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="wastebank",
            name="osm_id",
        ),
    ]
