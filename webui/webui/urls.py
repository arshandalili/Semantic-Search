"""webui URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from search.views import *


schema_view = get_schema_view(
    openapi.Info(
        title="Semantic Search API",
        default_version='v1',
        description="API for performing semantic search on a text corpus",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('', include('search.urls')),
    path('semantic/', include('semantic.urls')),
    path('admin/', admin.site.urls),
    path('search/', CorpusEntryViewSet.as_view({'get': 'semantic_search'}), name='semantic_search'),
    path('addentry/', CorpusEntryViewSet.as_view({'get': 'add_new_entry'}), name='add_new_entry'),
    path('deleteentry/', CorpusEntryViewSet.as_view({'get': 'delete_entry'}), name='delete_entry'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
