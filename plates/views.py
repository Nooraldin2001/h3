from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Q
from django.db.models.functions import Length
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.http import Http404, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.urls import reverse
from datetime import timedelta
import json
from decimal import Decimal, InvalidOperation

from .decorators import live_auction_enabled, superuser_required
from .models import Plate, Emirate, PlateType, Slider, Page, SiteSettings, LiveBroadcastSession
from .forms import ContactForm, SellPlateForm


def home(request):
	slides = Slider.objects.filter(is_active=True).order_by("-created_at")[:5]
	context = {"emirates": Emirate.objects.all(), "types": PlateType.objects.all(), "slides": slides}
	return render(request, "plates/home.html", context)


def _filtered_queryset(request):
	queryset = Plate.objects.select_related("emirate", "plate_type").all()
	emirate = request.GET.get("emirate")
	ptype = request.GET.get("type")
	letter = request.GET.get("letter")
	contains = request.GET.get("search")
	min_price = request.GET.get("min_price")
	max_price = request.GET.get("max_price")
	starts_with = request.GET.get("starts_with")
	ends_with = request.GET.get("ends_with")
	numbers_count = request.GET.get("numbers_count")

	if emirate:
		queryset = queryset.filter(emirate__slug=emirate)
	if ptype:
		queryset = queryset.filter(plate_type__slug=ptype)
	if letter:
		queryset = queryset.filter(code__iexact=letter)
	if contains:
		queryset = queryset.filter(number__icontains=contains)
	if starts_with:
		queryset = queryset.filter(number__istartswith=starts_with)
	if ends_with:
		queryset = queryset.filter(number__iendswith=ends_with)
	if min_price:
		queryset = queryset.filter(price_aed__gte=min_price)
	if max_price:
		queryset = queryset.filter(price_aed__lte=max_price)
	if numbers_count:
		try:
			count = int(numbers_count)
			queryset = queryset.annotate(num_len=Length("number")).filter(num_len=count)
		except Exception:
			pass
	return queryset


def plates_list_partial(request):
	queryset = _filtered_queryset(request)
	paginator = Paginator(queryset, 12)
	page_number = request.GET.get("page") or 1
	page_obj = paginator.get_page(page_number)
	return render(
		request,
		"plates/partials/_list_wrapper.html",
		{"page_obj": page_obj, "plates": page_obj.object_list},
	)


def page_detail(request, slug: str):
	page = get_object_or_404(Page, slug=slug)
	return render(request, "pages/page.html", {"page": page})


def contact(request):
	if request.method == 'POST':
		form = ContactForm(request.POST)
		if form.is_valid():
			# Get site settings for email
			site_settings = SiteSettings.objects.first()
			
			# Send email
			subject = f"Contact Form: {form.cleaned_data['subject']}"
			message = f"""
Name: {form.cleaned_data['name']}
Email: {form.cleaned_data['email']}
Phone: {form.cleaned_data.get('phone', 'Not provided')}

Message:
{form.cleaned_data['message']}
"""
			recipient = site_settings.email if site_settings and site_settings.email else settings.DEFAULT_FROM_EMAIL
			
			try:
				send_mail(
					subject,
					message,
					settings.DEFAULT_FROM_EMAIL,
					[recipient],
					fail_silently=False,
				)
				messages.success(request, _('Thank you! Your message has been sent successfully.'))
				form = ContactForm()  # Reset form
			except Exception as e:
				messages.error(request, _('Sorry, there was an error sending your message. Please try again later.'))
	else:
		form = ContactForm()
	
	return render(request, 'plates/contact.html', {'form': form})


def sell_plate(request):
	if request.method == 'POST':
		form = SellPlateForm(request.POST, request.FILES)
		if form.is_valid():
			# Get site settings for email
			site_settings = SiteSettings.objects.first()
			
			# Prepare email content
			subject = f"New Plate Listing: {form.cleaned_data['code']} {form.cleaned_data['number']}"
			message = f"""
New Plate Listing Submission

Seller Information:
Name: {form.cleaned_data['seller_name']}
Email: {form.cleaned_data['seller_email']}
Phone: {form.cleaned_data['seller_phone']}
WhatsApp: {form.cleaned_data.get('seller_whatsapp', 'Not provided')}

Plate Details:
Emirate: {form.cleaned_data['emirate']}
Plate Type: {form.cleaned_data['plate_type']}
Code: {form.cleaned_data['code']}
Number: {form.cleaned_data['number']}
Asking Price: {form.cleaned_data.get('price_aed', 'Not specified')} AED

Additional Notes:
{form.cleaned_data.get('additional_notes', 'None')}
"""
			recipient = site_settings.email if site_settings and site_settings.email else settings.DEFAULT_FROM_EMAIL
			
			try:
				# Send email
				send_mail(
					subject,
					message,
					settings.DEFAULT_FROM_EMAIL,
					[recipient],
					fail_silently=False,
				)
				
				# If image was uploaded, we could save it or attach it to email
				# For now, we'll just send the email notification
				
				messages.success(request, _('Thank you! Your plate listing has been submitted successfully. We will contact you soon.'))
				form = SellPlateForm()  # Reset form
			except Exception as e:
				messages.error(request, _('Sorry, there was an error submitting your plate listing. Please try again later.'))
	else:
		form = SellPlateForm()
	
	return render(request, 'plates/sell_plate.html', {'form': form})


def draw_plate(request):
	"""Render the draw your plate page"""
	emirates = Emirate.objects.all()
	plate_types = PlateType.objects.all()
	
	# Get available codes/letters
	codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
	         'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
	         'AA', 'BB', 'CC', 'DD', 'EE', 'FF', '?']
	
	context = {
		'emirates': emirates,
		'plate_types': plate_types,
		'codes': codes,
	}
	return render(request, 'plates/draw_plate.html', context)


def live_auction_test(request):
	"""
	Hidden Live Auction page at /test (unlisted + noindex).

	Hiding rules:
	- If LIVE_AUCTION_TEST_ENABLED is False -> 404
	- If DEBUG True -> allow (for local dev)
	- If LIVE_AUCTION_TEST_PUBLIC True -> allow (public test page)
	- Otherwise require ?k=<LIVE_AUCTION_TEST_TOKEN> (and if token is empty -> 404)
	"""
	if not getattr(settings, "LIVE_AUCTION_TEST_ENABLED", True):
		raise Http404()

	if getattr(settings, "DEBUG", False) or getattr(settings, "LIVE_AUCTION_TEST_PUBLIC", False):
		allowed = True
	else:
		token = (getattr(settings, "LIVE_AUCTION_TEST_TOKEN", "") or "").strip()
		allowed = bool(token) and request.GET.get("k") == token

	if not allowed:
		raise Http404()

	# Placeholder timing/data (replace later with real auction data)
	auction_end = timezone.now() + timedelta(hours=6)

	context = {
		"auction_end_iso": auction_end.isoformat(),
		# UI-only filter options (kept DB-free intentionally for this hidden test page)
		"emirate_options": [
			{"value": "abu-dhabi", "label_en": "Abu Dhabi", "label_ar": "أبوظبي"},
			{"value": "dubai", "label_en": "Dubai", "label_ar": "دبي"},
			{"value": "sharjah", "label_en": "Sharjah", "label_ar": "الشارقة"},
			{"value": "ajman", "label_en": "Ajman", "label_ar": "عجمان"},
			{"value": "ras-al-khaimah", "label_en": "Ras Al Khaimah", "label_ar": "رأس الخيمة"},
			{"value": "fujairah", "label_en": "Fujairah", "label_ar": "الفجيرة"},
			{"value": "umm-al-quwain", "label_en": "Umm Al Quwain", "label_ar": "أم القيوين"},
		],
		"lots": [
			{
				"lot": "01",
				"emirate": "Dubai",
				"code": "AA",
				"number": "777",
				"current": "85,000",
				"min_inc": "1,000",
				"bids": "66",
				"end_iso": auction_end.isoformat(),
			},
			{
				"lot": "02",
				"emirate": "Abu Dhabi",
				"code": "5",
				"number": "12345",
				"current": "12,000",
				"min_inc": "500",
				"bids": "29",
				"end_iso": auction_end.isoformat(),
			},
			{
				"lot": "03",
				"emirate": "Sharjah",
				"code": "12",
				"number": "9",
				"current": "250,000",
				"min_inc": "5,000",
				"bids": "14",
				"end_iso": auction_end.isoformat(),
			},
			{
				"lot": "04",
				"emirate": "Ajman",
				"code": "B",
				"number": "4040",
				"current": "3,400",
				"min_inc": "200",
				"bids": "2",
				"end_iso": auction_end.isoformat(),
			},
		],
	}

	response = render(request, "plates/live_auction_test.html", context)
	response["X-Robots-Tag"] = "noindex, nofollow"
	return response


def _get_or_create_live_session(user):
	session, _ = LiveBroadcastSession.objects.get_or_create(user=user)
	return session


def _serialize_live_session(session):
	remaining = 0
	timer_active = False
	if session.timer_ends_at:
		delta = session.timer_ends_at - timezone.now()
		remaining = max(0, int(delta.total_seconds()))
		timer_active = remaining > 0

	logo_url = session.logo.url if session.logo else ""
	price_str = ""
	if session.price is not None:
		if session.price == session.price.to_integral_value():
			price_str = str(int(session.price))
		else:
			price_str = str(session.price)

	return {
		"plate_type": session.plate_type,
		"code": session.code,
		"number": session.number,
		"phone_number": session.phone_number or "",
		"price": price_str,
		"message": session.message,
		"alert_message": session.alert_message,
		"event_title": session.event_title,
		"logo_url": logo_url,
		"timer_seconds": session.timer_seconds,
		"timer_remaining_seconds": remaining,
		"timer_active": timer_active,
		"display_token": str(session.display_token),
		"sold_event_id": session.sold_event_id,
		"sold_event_at": session.sold_event_at.isoformat() if session.sold_event_at else "",
		"sold_style": session.sold_style or LiveBroadcastSession.SOLD_STYLE_CONFETTI,
		"sold_name": session.sold_name or "",
		"tiktok_brand_mode": session.tiktok_brand_mode or LiveBroadcastSession.TIKTOK_BRAND_LOGO,
	}


def _get_session_for_api(request):
	token = request.GET.get("token") or request.POST.get("token")
	if request.user.is_authenticated and request.user.is_superuser:
		return _get_or_create_live_session(request.user)
	if token:
		try:
			return LiveBroadcastSession.objects.get(display_token=token)
		except LiveBroadcastSession.DoesNotExist:
			return None
	return None


@method_decorator(live_auction_enabled, name="dispatch")
class LiveLoginView(LoginView):
	template_name = "plates/live_login.html"
	redirect_authenticated_user = True

	def get_success_url(self):
		return "/live/"


@live_auction_enabled
@superuser_required
def live_control(request):
	session = _get_or_create_live_session(request.user)
	token = session.display_token
	context = {
		"session": session,
		"display_url": request.build_absolute_uri(reverse("live_display", kwargs={"token": token})),
		"display_new_url": request.build_absolute_uri(reverse("live_display_new", kwargs={"token": token})),
		"display_tiktok_url": request.build_absolute_uri(reverse("live_display_tiktok", kwargs={"token": token})),
	}
	return render(request, "plates/live_hub.html", context)


def _live_control_panel_context(request, mode):
	session = _get_or_create_live_session(request.user)
	token = session.display_token
	urls = {
		"classic": request.build_absolute_uri(reverse("live_display", kwargs={"token": token})),
		"new": request.build_absolute_uri(reverse("live_display_new", kwargs={"token": token})),
		"tiktok": request.build_absolute_uri(reverse("live_display_tiktok", kwargs={"token": token})),
	}
	titles = {
		"classic": "Classic display control",
		"new": "New style display control",
		"tiktok": "TikTok display control",
	}
	return {
		"session": session,
		"control_mode": mode,
		"control_title": titles[mode],
		"display_url": urls[mode],
		"display_url_classic": urls["classic"],
		"display_url_new": urls["new"],
		"display_url_tiktok": urls["tiktok"],
		"plate_types": LiveBroadcastSession.PLATE_TYPE_CHOICES,
		"timer_mins": session.timer_seconds // 60,
		"timer_secs": session.timer_seconds % 60,
		"state_json": json.dumps(_serialize_live_session(session)),
		"show_event_title": mode in ("new", "tiktok"),
		"show_tiktok_brand": mode == "tiktok",
		"show_logo_upload": mode in ("new", "tiktok"),
	}


@live_auction_enabled
@superuser_required
def live_control_classic(request):
	return render(request, "plates/live_control_panel.html", _live_control_panel_context(request, "classic"))


@live_auction_enabled
@superuser_required
def live_control_new(request):
	return render(request, "plates/live_control_panel.html", _live_control_panel_context(request, "new"))


@live_auction_enabled
@superuser_required
def live_control_tiktok(request):
	return render(request, "plates/live_control_panel.html", _live_control_panel_context(request, "tiktok"))


@live_auction_enabled
def live_display(request, token):
	try:
		session = LiveBroadcastSession.objects.get(display_token=token)
	except LiveBroadcastSession.DoesNotExist:
		raise Http404()
	context = {
		"token": str(token),
		"state_json": json.dumps(_serialize_live_session(session)),
	}
	response = render(request, "plates/live_display.html", context)
	response["X-Robots-Tag"] = "noindex, nofollow"
	return response


@live_auction_enabled
def live_display_new(request, token):
	try:
		session = LiveBroadcastSession.objects.get(display_token=token)
	except LiveBroadcastSession.DoesNotExist:
		raise Http404()
	context = {
		"token": str(token),
		"state_json": json.dumps(_serialize_live_session(session)),
	}
	response = render(request, "plates/live_display_new.html", context)
	response["X-Robots-Tag"] = "noindex, nofollow"
	return response


@live_auction_enabled
def live_display_tiktok(request, token):
	try:
		session = LiveBroadcastSession.objects.get(display_token=token)
	except LiveBroadcastSession.DoesNotExist:
		raise Http404()
	context = {
		"token": str(token),
		"state_json": json.dumps(_serialize_live_session(session)),
	}
	response = render(request, "plates/live_display_tiktok.html", context)
	response["X-Robots-Tag"] = "noindex, nofollow"
	return response


@live_auction_enabled
@require_http_methods(["GET", "PATCH"])
def live_state_api(request):
	if request.method == "GET":
		session = _get_session_for_api(request)
		if not session:
			return JsonResponse({"error": "Unauthorized"}, status=403)
		return JsonResponse(_serialize_live_session(session))

	if not request.user.is_authenticated or not request.user.is_superuser:
		return JsonResponse({"error": "Unauthorized"}, status=403)

	session = _get_or_create_live_session(request.user)

	try:
		data = json.loads(request.body.decode("utf-8") or "{}")
	except json.JSONDecodeError:
		return JsonResponse({"error": "Invalid JSON"}, status=400)

	if "plate_type" in data:
		valid = {c[0] for c in LiveBroadcastSession.PLATE_TYPE_CHOICES}
		if data["plate_type"] in valid:
			session.plate_type = data["plate_type"]
	if "code" in data:
		session.code = str(data["code"])[:10]
	if "number" in data:
		session.number = str(data["number"])[:10]
	if "phone_number" in data:
		session.phone_number = str(data["phone_number"])[:30]
	if "message" in data:
		session.message = str(data["message"])[:500]
	if "alert_message" in data:
		session.alert_message = str(data["alert_message"])[:500]
	if "event_title" in data:
		session.event_title = str(data["event_title"])[:200]
	if "sold_name" in data:
		session.sold_name = str(data["sold_name"])[:120]
	if "tiktok_brand_mode" in data:
		allowed_brand = {c[0] for c in LiveBroadcastSession.TIKTOK_BRAND_CHOICES}
		if data["tiktok_brand_mode"] in allowed_brand:
			session.tiktok_brand_mode = data["tiktok_brand_mode"]
	if "price" in data:
		raw = data["price"]
		if raw in (None, ""):
			session.price = None
		else:
			try:
				session.price = Decimal(str(raw).replace(",", ""))
			except (InvalidOperation, ValueError):
				pass
	if "timer_seconds" in data:
		try:
			session.timer_seconds = max(1, int(data["timer_seconds"]))
		except (TypeError, ValueError):
			pass
	if data.get("start_timer"):
		session.timer_ends_at = timezone.now() + timedelta(seconds=session.timer_seconds)
	if data.get("stop_timer"):
		session.timer_ends_at = None
	if data.get("clear_logo"):
		if session.logo:
			session.logo.delete(save=False)
			session.logo = None
	if data.get("trigger_sold"):
		session.sold_event_id = (session.sold_event_id or 0) + 1
		session.sold_event_at = timezone.now()
		style = data.get("sold_style") or LiveBroadcastSession.SOLD_STYLE_CONFETTI
		allowed = {choice[0] for choice in LiveBroadcastSession.SOLD_STYLE_CHOICES}
		session.sold_style = style if style in allowed else LiveBroadcastSession.SOLD_STYLE_CONFETTI
		if "sold_name" in data:
			session.sold_name = str(data["sold_name"])[:120]

	session.save()
	return JsonResponse(_serialize_live_session(session))


@live_auction_enabled
@superuser_required
@require_http_methods(["POST", "DELETE"])
def live_logo_upload(request):
	session = _get_or_create_live_session(request.user)
	if request.method == "DELETE" or request.POST.get("clear_logo"):
		if session.logo:
			session.logo.delete(save=False)
			session.logo = None
			session.save(update_fields=["logo"])
		return JsonResponse(_serialize_live_session(session))
	if "logo" not in request.FILES:
		return JsonResponse({"error": "No logo file"}, status=400)
	session.logo = request.FILES["logo"]
	session.save()
	return JsonResponse(_serialize_live_session(session))

