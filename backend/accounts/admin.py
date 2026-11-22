from django.contrib import admin

from accounts.models import CustomerAddress, CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "phone_number", "created_at")
    search_fields = ("email", "phone_number", "user__first_name", "user__last_name")
    ordering = ("email",)
    autocomplete_fields = ("user",)


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "customer",
        "city",
        "state",
        "address_type",
        "is_default",
    )
    search_fields = (
        "full_name",
        "phone_number",
        "city",
        "postal_code",
        "customer__email",
    )
    list_filter = ("address_type", "is_default", "state")
    ordering = ("customer__email", "-is_default", "-updated_at")
    autocomplete_fields = ("customer",)
    readonly_fields = ("is_default",)
