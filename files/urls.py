from django.urls import include, path
from rest_framework import routers

from files.views import FileViewSet,FileDeleteBulkViewSet

app_name = "files"


router = routers.SimpleRouter()
router.register(r"files", FileViewSet)
router.register(r"delete-files", FileDeleteBulkViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
