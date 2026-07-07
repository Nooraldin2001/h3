from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0002_livebroadcastsession"),
    ]

    operations = [
        migrations.AddField(
            model_name="livebroadcastsession",
            name="alert_message",
            field=models.CharField(
                blank=True,
                default="⚠️ لا تحول عربون نهائياً وقم بالتنازل عن الرقم في المرور فقط ⚠️",
                max_length=500,
            ),
        ),
    ]
