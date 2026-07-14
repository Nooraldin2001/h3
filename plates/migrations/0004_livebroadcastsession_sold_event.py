from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0003_livebroadcastsession_alert_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="livebroadcastsession",
            name="sold_event_id",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="livebroadcastsession",
            name="sold_event_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
