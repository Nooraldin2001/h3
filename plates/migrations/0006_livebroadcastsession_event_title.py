from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plates", "0005_livebroadcastsession_sold_style"),
    ]

    operations = [
        migrations.AddField(
            model_name="livebroadcastsession",
            name="event_title",
            field=models.CharField(
                blank=True,
                default="مزاد علني مباشر لبيع وشراء الأرقام المميزة",
                max_length=200,
            ),
        ),
    ]
