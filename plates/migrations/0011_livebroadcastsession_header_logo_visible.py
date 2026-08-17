from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0010_livebroadcastsession_phone_number_du_etisalat"),
    ]

    operations = [
        migrations.AddField(
            model_name="livebroadcastsession",
            name="header_logo_visible",
            field=models.BooleanField(default=True),
        ),
    ]
