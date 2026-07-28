from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("<int:notification_id>/open/", views.open_notification, name="open"),
    path("unread-count/", views.unread_count, name="unread_count"),
    path("mark-all-read/", views.mark_all_read, name="mark_all_read"),
]
