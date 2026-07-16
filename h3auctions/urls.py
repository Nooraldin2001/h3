from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from sitemaps import PlateSitemap, PageSitemap
from plates import views as plate_views
from plates.decorators import live_auction_enabled

urlpatterns = [
	path("i18n/", include("django.conf.urls.i18n")),
	# Hidden live auction test page (not i18n-prefixed)
	path("test", plate_views.live_auction_test, name="live_auction_test"),
	path("test/", plate_views.live_auction_test, name="live_auction_test_slash"),
	# Live auction studio
	path("live/login/", plate_views.LiveLoginView.as_view(), name="live_login"),
	path("live/logout/", live_auction_enabled(LogoutView.as_view(next_page="/live/login/")), name="live_logout"),
	path("live/", plate_views.live_control, name="live_control"),
	path("live/control/classic/", plate_views.live_control_classic, name="live_control_classic"),
	path("live/control/new/", plate_views.live_control_new, name="live_control_new"),
	path("live/control/tiktok/", plate_views.live_control_tiktok, name="live_control_tiktok"),
	path("live/display/<uuid:token>/", plate_views.live_display, name="live_display"),
	path("live/display-new/<uuid:token>/", plate_views.live_display_new, name="live_display_new"),
	path("live/display-tiktok/<uuid:token>/", plate_views.live_display_tiktok, name="live_display_tiktok"),
	path("live/api/state/", plate_views.live_state_api, name="live_state_api"),
	path("live/api/logo/", plate_views.live_logo_upload, name="live_logo_upload"),
]

urlpatterns += i18n_patterns(
	path("admin/", admin.site.urls),
	path("", include("plates.urls")),
)

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Sitemap (not i18n-wrapped so it's accessible at root)
sitemaps = {"plates": PlateSitemap, "pages": PageSitemap}
urlpatterns += [
	path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]


