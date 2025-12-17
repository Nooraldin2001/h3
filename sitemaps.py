from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from plates.models import Plate, Page


class PlateSitemap(Sitemap):
	changefreq = "daily"
	priority = 0.6

	def items(self):
		return Plate.objects.all()

	def location(self, obj):
		# placeholder: could add slugged detail url later
		return reverse("plates:home") + f"?plate={obj.id}"


class PageSitemap(Sitemap):
	changefreq = "monthly"
	priority = 0.5

	def items(self):
		return Page.objects.all()

	def location(self, obj):
		return reverse("plates:page", kwargs={"slug": obj.slug})





