from django.conf import settings


class AutoSilkProfileMiddleware:
    """Auto-profile all views"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.silk_available = False

        if settings.DEBUG:
            try:
                from silk.profiling.profiler import silk_profile
                self.silk_profile = silk_profile
                self.silk_available = True
            except ImportError:
                pass

    def __call__(self, request):
        if not self.silk_available:
            return self.get_response(request)

        view_name = self._get_view_name(request)

        with self.silk_profile(name=view_name):
            response = self.get_response(request)

        return response

    def _get_view_name(self, request):
        try:
            from django.urls import resolve
            resolved = resolve(request.path_info)

            if hasattr(resolved.func, 'view_class'):
                # CBV
                return resolved.func.view_class.__name__
            elif hasattr(resolved.func, '__name__'):
                # FBV
                return resolved.func.__name__
            else:
                return resolved.view_name or request.path
        except:
            return request.path