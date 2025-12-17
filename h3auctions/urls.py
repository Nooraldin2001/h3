from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from sitemaps import PlateSitemap, PageSitemap

urlpatterns = [
	path("i18n/", include("django.conf.urls.i18n")),
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


