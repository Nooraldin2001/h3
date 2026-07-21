from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0009_alter_livebroadcastsession_tiktok_brand_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="livebroadcastsession",
            name="phone_number",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AlterField(
            model_name="livebroadcastsession",
            name="plate_type",
            field=models.CharField(
                choices=[
                    ("abudhabi", "Abu Dhabi"),
                    ("dubai", "Dubai"),
                    ("dubai_yellow", "Dubai Yellow"),
                    ("sharjah", "Sharjah"),
                    ("ajman", "Ajman"),
                    ("rasalkhimma", "Ras Al Khaimah"),
                    ("ummalquain", "Umm Al Quwain"),
                    ("fujairah", "Fujairah"),
                    ("du", "du"),
                    ("etisalat", "Etisalat"),
                ],
                default="abudhabi",
                max_length=20,
            ),
        ),
    ]
