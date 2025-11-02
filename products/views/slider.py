from rest_framework import viewsets

from core.permissions import IsAdminUserOrReadOnly
from core.utils import StandardLimitOffsetPagination
from products.models import Slider
from products.serializers import SliderSerializer


class SliderViews(viewsets.ModelViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = Slider.objects.all()
    serializer_class = SliderSerializer
    model_object = Slider
    pagination_class = StandardLimitOffsetPagination
