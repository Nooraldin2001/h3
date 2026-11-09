# Generated manually for New Style dedicated display token

import uuid

from django.db import migrations, models


def populate_new_style_tokens(apps, schema_editor):
	LiveBroadcastSession = apps.get_model("plates", "LiveBroadcastSession")
	for session in LiveBroadcastSession.objects.all().iterator():
		session.new_style_display_token = uuid.uuid4()
		session.save(update_fields=["new_style_display_token"])


class Migration(migrations.Migration):

	dependencies = [
		("plates", "0012_livebroadcastsession_new_style_fireworks"),
	]

	operations = [
		migrations.AddField(
			model_name="livebroadcastsession",
			name="new_style_display_token",
			field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
		),
		migrations.RunPython(populate_new_style_tokens, migrations.RunPython.noop),
		migrations.AlterField(
			model_name="livebroadcastsession",
			name="new_style_display_token",
			field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
		),
	]
