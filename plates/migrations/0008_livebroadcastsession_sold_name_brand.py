from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0007_clear_custom_live_logos"),
    ]

    operations = [
        migrations.AddField(
            model_name="livebroadcastsession",
            name="sold_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="livebroadcastsession",
            name="tiktok_brand_mode",
            field=models.CharField(
                choices=[("logo", "Logo"), ("watermark", "Watermark")],
                default="logo",
                max_length=20,
            ),
        ),
    ]
