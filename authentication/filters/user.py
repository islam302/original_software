from django.contrib.auth import get_user_model
from django.utils import timezone
from django_filters import rest_framework as rest_framework_filters


class UserFilter(rest_framework_filters.FilterSet):
    class Meta:
        model = get_user_model()
        fields = [
            "is_active",
            "hidden",
        ]
        
class UserCustomFilterBackend:

    def filter_queryset(self, request, queryset, view):
        type = request.query_params.get("type", None)
        
        if type == "admin":
            queryset = queryset.filter(is_staff=True)
        elif type == "user":
            queryset = queryset.filter(is_staff=False).filter(is_whoelsale=False)
        elif type == "wholesale":
            queryset = queryset.filter(is_staff=False).filter(wholesale_type_id__isnull=False)
        

        return queryset



