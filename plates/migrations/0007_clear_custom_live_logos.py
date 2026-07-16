from django.db import migrations


def clear_custom_logos(apps, schema_editor):
	LiveBroadcastSession = apps.get_model("plates", "LiveBroadcastSession")
	for session in LiveBroadcastSession.objects.all():
		if session.logo:
			session.logo = None
			session.save(update_fields=["logo"])


def noop_reverse(apps, schema_editor):
	pass


class Migration(migrations.Migration):

	dependencies = [
		("plates", "0006_livebroadcastsession_event_title"),
	]

	operations = [
		migrations.RunPython(clear_custom_logos, noop_reverse),
	]
