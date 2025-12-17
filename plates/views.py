from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Q
from django.db.models.functions import Length
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import Plate, Emirate, PlateType, Slider, Page, SiteSettings
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
	         'AA', 'BB', 'CC', 'DD', 'EE', '?']
	
	context = {
		'emirates': emirates,
		'plate_types': plate_types,
		'codes': codes,
	}
	return render(request, 'plates/draw_plate.html', context)

