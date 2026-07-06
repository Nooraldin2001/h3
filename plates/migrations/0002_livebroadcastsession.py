import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("plates", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LiveBroadcastSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("display_token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                (
                    "plate_type",
                    models.CharField(
                        choices=[
                            ("abudhabi", "Abu Dhabi"),
                            ("dubai", "Dubai"),
                            ("dubai_yellow", "Dubai Yellow"),
                            ("sharjah", "Sharjah"),
                            ("ajman", "Ajman"),
                            ("rasalkhimma", "Ras Al Khaimah"),
                            ("ummalquain", "Umm Al Quwain"),
                            ("fujairah", "Fujairah"),
                        ],
                        default="abudhabi",
                        max_length=20,
                    ),
                ),
                ("code", models.CharField(blank=True, default="", max_length=10)),
                ("number", models.CharField(blank=True, default="", max_length=10)),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("message", models.CharField(blank=True, default="", max_length=500)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="live/logos/")),
                ("timer_seconds", models.PositiveIntegerField(default=60)),
                ("timer_ends_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="live_broadcast_session",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Live Broadcast Session",
                "verbose_name_plural": "Live Broadcast Sessions",
            },
        ),
    ]
