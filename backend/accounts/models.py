from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


phone_number_validator = RegexValidator(
    regex=r"^\+?[1-9]\d{6,14}$",
    message="Enter a phone number with 7 to 15 digits, optionally prefixed by +.",
)
postal_code_validator = RegexValidator(
    regex=r"^[1-9]\d{5}$",
    message="Enter a valid 6-digit Indian postal code.",
)


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email


class CustomerAddress(models.Model):
    class AddressType(models.TextChoices):
        HOME = "home", "Home"
        WORK = "work", "Work"
        OTHER = "other", "Other"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delivery_addresses",
    )
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(
        max_length=20,
        validators=[phone_number_validator],
    )
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=6, validators=[postal_code_validator])
    address_type = models.CharField(
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.HOME,
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-updated_at", "-pk"]
        indexes = [
            models.Index(
                fields=["customer", "is_default"],
                name="accounts_addr_default",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.city} ({self.customer})"
