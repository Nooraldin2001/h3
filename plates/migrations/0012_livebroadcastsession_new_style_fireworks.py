from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0011_livebroadcastsession_header_logo_visible"),
    ]

    operations = [
        migrations.AddField(
            model_name="livebroadcastsession",
            name="new_style",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="livebroadcastsession",
            name="sold_style",
            field=models.CharField(
                choices=[
                    ("confetti", "Confetti"),
                    ("gavel", "Gavel"),
                    ("fireworks", "Fireworks"),
                ],
                default="confetti",
                max_length=20,
            ),
        ),
    ]
