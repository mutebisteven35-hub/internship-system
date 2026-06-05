from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from django.views.generic import TemplateView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]

if settings.FRONTEND_INDEX.exists():
    urlpatterns += [
        re_path(
            r"^(?!(?:api|admin|static|media)(?:/|$)).*$",
            TemplateView.as_view(template_name="index.html"),
            name="frontend",
        ),
    ]
