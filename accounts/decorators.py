from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='client_login')
        def _wrapped_view(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)

            if profile and profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            return redirect('role_redirect')

        return _wrapped_view
    return decorator