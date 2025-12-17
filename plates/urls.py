from django.urls import path
from . import views

app_name = "plates"

urlpatterns = [
	path("", views.home, name="home"),
	path("htmx/list/", views.plates_list_partial, name="plates_list_partial"),
	path("page/<slug:slug>/", views.page_detail, name="page"),
	path("contact/", views.contact, name="contact"),
	path("sell/", views.sell_plate, name="sell_plate"),
	path("draw-plate/", views.draw_plate, name="draw_plate"),
]


