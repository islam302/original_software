from django.contrib import admin

from files.models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = ("file",)
    search_fields = ("file",)
    fieldsets = (
        (
            None,
            {"fields": ("file",)},
        ),
        (
            "Technical Info",
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "updated_by",
                )
            },
        ),
    )
