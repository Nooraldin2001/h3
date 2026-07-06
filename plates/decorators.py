from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import Http404, HttpResponseForbidden


def live_auction_enabled(view_func):
	@wraps(view_func)
	def _wrapped(request, *args, **kwargs):
		from django.conf import settings
		if not getattr(settings, "LIVE_AUCTION_ENABLED", True):
			raise Http404()
		return view_func(request, *args, **kwargs)
	return _wrapped


def superuser_required(view_func):
	@wraps(view_func)
	def _wrapped(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect_to_login(request.get_full_path(), login_url="/live/login/")
		if not request.user.is_superuser:
			return HttpResponseForbidden("Superuser access required.")
		return view_func(request, *args, **kwargs)
	return _wrapped
