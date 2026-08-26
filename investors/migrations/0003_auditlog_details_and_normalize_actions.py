from django.db import migrations, models


ACTION_NORMALIZE = {
    "Created": "uploaded",
    "created": "uploaded",
    "Create": "uploaded",
    "create": "uploaded",
    "Updated": "edited",
    "updated": "edited",
    "Update": "edited",
    "update": "edited",
    "Edited": "edited",
    "Deleted": "deleted",
    "deleted": "deleted",
    "Delete": "deleted",
    "delete": "deleted",
}


def normalize_actions(apps, schema_editor):
    AuditLog = apps.get_model("investors", "AuditLog")
    for old, new in ACTION_NORMALIZE.items():
        AuditLog.objects.filter(action=old).update(action=new)

    AuditLog.objects.filter(action="deleted", details="").update(details="Document deleted")
    AuditLog.objects.filter(action="edited", details="").update(details="Document details updated")
    AuditLog.objects.filter(action="uploaded", details="").update(details="New document uploaded")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("investors", "0002_auditlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="details",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(normalize_actions, noop),
    ]
