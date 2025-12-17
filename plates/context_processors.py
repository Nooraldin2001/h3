from .models import SiteSettings


def site_settings(request):
	settings_obj = SiteSettings.objects.first()
	return {"SITE_SETTINGS": settings_obj}





