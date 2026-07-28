from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path("settings/<str:section>/", views.settings_view, name="settings"),
    path("settings/unblock/<int:user_id>/", views.unblock_user, name="unblock_user"),
    path("support/<str:page>/", views.support_view, name="support"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/accounts/profile/",
        ),
        name="password_change",
    ),
]
