import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class Emirate(TranslatableModel):
	slug = models.SlugField(unique=True, max_length=50)
	translations = TranslatedFields(
		name=models.CharField(max_length=100)
	)

	class Meta:
		verbose_name = _("Emirate")
		verbose_name_plural = _("Emirates")

	def __str__(self) -> str:
		return self.safe_translation_getter("name", any_language=True) or self.slug


class PlateType(TranslatableModel):
	slug = models.SlugField(unique=True, max_length=50)
	translations = TranslatedFields(
		name=models.CharField(max_length=100)
	)

	class Meta:
		verbose_name = _("Plate Type")
		verbose_name_plural = _("Plate Types")

	def __str__(self) -> str:
		return self.safe_translation_getter("name", any_language=True) or self.slug


class Plate(TimeStampedModel):
	emirate = models.ForeignKey(Emirate, on_delete=models.PROTECT, related_name="plates")
	plate_type = models.ForeignKey(PlateType, on_delete=models.PROTECT, related_name="plates")
	code = models.CharField(max_length=10, help_text=_("Letter/code e.g. F, AA, 1"))
	number = models.CharField(max_length=10, help_text=_("Digits/characters as displayed"))
	price_aed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	contact_tel = models.CharField(max_length=20)
	contact_whatsapp = models.CharField(max_length=20, blank=True, help_text=_("Without spaces, e.g. +9715xxxxxxx"))
	is_featured = models.BooleanField(default=False)
	image = models.ImageField(upload_to="plates/", blank=True, null=True)

	class Meta:
		indexes = [
			models.Index(fields=["code"]),
			models.Index(fields=["number"]),
		]
		ordering = ["-is_featured", "-created_at"]

	def __str__(self) -> str:
		return f"{self.code} {self.number}"

	def has_price(self) -> bool:
		return self.price_aed is not None


class Slider(TimeStampedModel, TranslatableModel):
	image = models.ImageField(upload_to="slider/")
	link_url = models.URLField(blank=True)
	is_active = models.BooleanField(default=True)
	translations = TranslatedFields(
		alt=models.CharField(max_length=150, blank=True),
	)

	class Meta:
		verbose_name = _("Slider Image")
		verbose_name_plural = _("Slider Images")
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return self.safe_translation_getter("alt", any_language=True) or f"Slide {self.pk}"


class Page(TimeStampedModel, TranslatableModel):
	slug = models.SlugField(unique=True, max_length=60)
	translations = TranslatedFields(
		title=models.CharField(max_length=160),
		body=models.TextField(),
	)

	class Meta:
		verbose_name = _("Page")
		verbose_name_plural = _("Pages")

	def __str__(self) -> str:
		return self.safe_translation_getter("title", any_language=True) or self.slug


class SiteSettings(TranslatableModel):
	# singleton pattern: only one row expected
	logo = models.ImageField(upload_to="branding/", blank=True, null=True)
	primary_color = models.CharField(max_length=7, default="#6f41a4")
	secondary_color = models.CharField(max_length=7, default="#ffffff")
	phone = models.CharField(max_length=30, blank=True)
	email = models.EmailField(blank=True)
	instagram = models.URLField(blank=True)
	google_tag_id = models.CharField(max_length=30, blank=True)
	translations = TranslatedFields(
		address=models.CharField(max_length=255, blank=True),
	)

	class Meta:
		verbose_name = _("Site Settings")
		verbose_name_plural = _("Site Settings")

	def __str__(self) -> str:
		return "Settings"


class LiveBroadcastSession(TimeStampedModel):
	PLATE_TYPE_CHOICES = [
		("abudhabi", _("Abu Dhabi")),
		("dubai", _("Dubai")),
		("dubai_yellow", _("Dubai Yellow")),
		("sharjah", _("Sharjah")),
		("ajman", _("Ajman")),
		("rasalkhimma", _("Ras Al Khaimah")),
		("ummalquain", _("Umm Al Quwain")),
		("fujairah", _("Fujairah")),
	]

	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="live_broadcast_session",
	)
	display_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	plate_type = models.CharField(max_length=20, choices=PLATE_TYPE_CHOICES, default="abudhabi")
	code = models.CharField(max_length=10, blank=True, default="")
	number = models.CharField(max_length=10, blank=True, default="")
	price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	message = models.CharField(max_length=500, blank=True, default="")
	alert_message = models.CharField(
		max_length=500,
		blank=True,
		default="⚠️ لا تحول عربون نهائياً وقم بالتنازل عن الرقم في المرور فقط ⚠️",
	)
	event_title = models.CharField(
		max_length=200,
		blank=True,
		default="مزاد علني مباشر لبيع وشراء الأرقام المميزة",
	)
	logo = models.ImageField(upload_to="live/logos/", blank=True, null=True)
	timer_seconds = models.PositiveIntegerField(default=60)
	timer_ends_at = models.DateTimeField(null=True, blank=True)
	sold_event_id = models.PositiveIntegerField(default=0)
	sold_event_at = models.DateTimeField(null=True, blank=True)
	SOLD_STYLE_CONFETTI = "confetti"
	SOLD_STYLE_GAVEL = "gavel"
	SOLD_STYLE_CHOICES = (
		(SOLD_STYLE_CONFETTI, _("Confetti")),
		(SOLD_STYLE_GAVEL, _("Gavel")),
	)
	sold_style = models.CharField(
		max_length=20,
		choices=SOLD_STYLE_CHOICES,
		default=SOLD_STYLE_CONFETTI,
	)

	class Meta:
		verbose_name = _("Live Broadcast Session")
		verbose_name_plural = _("Live Broadcast Sessions")

	def __str__(self) -> str:
		return f"Live session for {self.user}"



