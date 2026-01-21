from .base import *


if DEBUG:
    ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")
    INTERNAL_IPS = os.getenv("DJANGO_INTERNAL_IPS", "127.0.0.1,localhost").split(",")  # could be replaced with plain ['x', 'y']

    PROFILING = os.getenv("DJANGO_PROFILING") == "1"
    if PROFILING:
        MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
        MIDDLEWARE.insert(0, 'silk.middleware.SilkyMiddleware')  # Silk has to catch FULL request and profile everything including other middleware
        MIDDLEWARE.insert(1, 'shared.middleware.auto_silk_profile_middleware.AutoSilkProfileMiddleware')

        INSTALLED_APPS.extend(['debug_toolbar', 'silk'])
        SILKY_PYTHON_PROFILER = True  # Enable cProfile for each query
        SILKY_PYTHON_PROFILER_BINARY = False  # saves data in binary format for visualizing Python`s calls (views layer)
        SILKY_PYTHON_PROFILER_RESULT_PATH = os.path.join(MEDIA_ROOT, 'silk/')