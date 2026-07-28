from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import (
    AppearanceSettingsForm, ChatSettingsForm, LoginForm,
    PrivacySettingsForm, ProfileForm, RegisterForm,
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("chat:dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        if not form.cleaned_data.get("remember_me"):
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(60 * 60 * 24 * 30)
        destination = request.POST.get("next") or request.GET.get("next")
        if not destination or not url_has_allowed_host_and_scheme(
            destination, allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            destination = "chat:dashboard"
        messages.success(request, f"Welcome back, {request.user.profile.name}.")
        return redirect(destination)
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been signed out securely.")
    return redirect("chat:welcome")

def register_view(request):
    if request.user.is_authenticated:
        return redirect("chat:dashboard")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created successfully.")
        return redirect("chat:dashboard")

    return render(request, "accounts/register.html", {"form": form})

@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")

@login_required
def edit_profile_view(request):
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user.profile,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("accounts:profile")

    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
def settings_view(request, section="privacy"):
    forms = {
        "privacy": PrivacySettingsForm,
        "chat": ChatSettingsForm,
        "appearance": AppearanceSettingsForm,
    }
    if section not in forms:
        return redirect("accounts:settings", section="privacy")
    form = forms[section](
        request.POST or None,
        request.FILES or None,
        instance=request.user.profile,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your settings have been saved.")
        return redirect("accounts:settings", section=section)
    return render(request, "accounts/settings.html", {
        "section": section,
        "form": form,
        "blocked_users": request.user.profile.blocked_users.select_related("profile"),
    })


@login_required
@require_POST
def unblock_user(request, user_id):
    request.user.profile.blocked_users.remove(user_id)
    messages.success(request, "Contact unblocked.")
    return redirect("accounts:settings", section="privacy")


@login_required
def support_view(request, page):
    allowed = {"help", "help-center", "contact", "terms", "app-info"}
    if page not in allowed:
        return redirect("accounts:support", page="help")
    return render(request, "accounts/support.html", {"support_page": page})
