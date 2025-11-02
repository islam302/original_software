from rest_framework import serializers

from core.serializer_fields import Base64ImageField
from products.models import Company
from django.db import transaction



class CompanySerializer(serializers.ModelSerializer):
    logo = Base64ImageField(required=False)

    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "name_ar",
            "logo",
            "show_in_home",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        
    def delete_bulk(validated_data):
        with transaction.atomic():
            companies = Company.objects.filter(id__in=validated_data["ids"])
            for company in companies:
                company.delete()
        
        return {"message": "Orders deleted successfully"}
