from django.shortcuts import render


def home(request):
    role = None
    if request.user.is_authenticated:
        try:
            role = request.user.profile.role
        except Exception:
            role = None

    return render(request, 'home.html', {'role': role})