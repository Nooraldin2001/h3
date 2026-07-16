from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0008_livebroadcastsession_sold_name_brand"),
    ]

    operations = [
        migrations.AlterField(
            model_name="livebroadcastsession",
            name="tiktok_brand_mode",
            field=models.CharField(
                choices=[
                    ("watermark", "Watermark"),
                    ("logo", "Logo"),
                    ("empty", "Empty"),
                ],
                default="logo",
                max_length=20,
            ),
        ),
    ]
