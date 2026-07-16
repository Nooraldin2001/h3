from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0004_livebroadcastsession_sold_event"),
    ]

    operations = [
        migrations.AddField(
            model_name="livebroadcastsession",
            name="sold_style",
            field=models.CharField(
                choices=[("confetti", "Confetti"), ("gavel", "Gavel")],
                default="confetti",
                max_length=20,
            ),
        ),
    ]
