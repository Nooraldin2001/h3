from django.contrib import admin
from django.utils.html import format_html
from parler.admin import TranslatableAdmin
from . import models


@admin.register(models.Emirate)
class EmirateAdmin(TranslatableAdmin):
	list_display = ("slug", "name")
	search_fields = ("translations__name", "slug")

	def name(self, obj):
		return obj.safe_translation_getter("name", any_language=True)


@admin.register(models.PlateType)
class PlateTypeAdmin(TranslatableAdmin):
	list_display = ("slug", "name")
	search_fields = ("translations__name", "slug")

	def name(self, obj):
		return obj.safe_translation_getter("name", any_language=True)


@admin.register(models.Plate)
class PlateAdmin(admin.ModelAdmin):
	list_display = ("id", "emirate", "plate_type", "code", "number", "price_aed", "is_featured", "thumb")
	list_filter = ("emirate", "plate_type", "is_featured")
	search_fields = ("code", "number", "contact_tel", "contact_whatsapp")
	autocomplete_fields = ("emirate", "plate_type",)

	def thumb(self, obj):
		if obj.image:
			return format_html('<img src="{}" style="height:40px;"/>', obj.image.url)
		return "-"


@admin.register(models.Slider)
class SliderAdmin(TranslatableAdmin):
	list_display = ("id", "is_active", "alt", "preview", "created_at")
	list_filter = ("is_active",)
	search_fields = ("translations__alt",)

	def alt(self, obj):
		return obj.safe_translation_getter("alt", any_language=True)

	def preview(self, obj):
		if obj.image:
			return format_html('<img src="{}" style="height:40px;"/>', obj.image.url)
		return "-"


@admin.register(models.Page)
class PageAdmin(TranslatableAdmin):
	list_display = ("slug", "title", "created_at")
	search_fields = ("slug", "translations__title")

	def title(self, obj):
		return obj.safe_translation_getter("title", any_language=True)


@admin.register(models.SiteSettings)
class SiteSettingsAdmin(TranslatableAdmin):
	list_display = ("id", "phone", "email", "address")

	def address(self, obj):
		return obj.safe_translation_getter("address", any_language=True)





