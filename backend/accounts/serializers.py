import re
import uuid

from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from accounts.models import CustomerAddress, CustomerProfile

User = get_user_model()
PHONE_PATTERN = re.compile(r"\+?[1-9]\d{6,14}\Z")


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        try:
            user_id = urlsafe_base64_decode(attrs["uid"]).decode()
            user = User.objects.get(pk=user_id)
        except (ValueError, TypeError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "This password reset link is invalid or expired."})
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "This password reset link is invalid or expired."})
        try:
            password_validation.validate_password(attrs["new_password"], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})
        attrs["user"] = user
        return attrs


def normalize_phone_number(value):
    normalized = re.sub(r"[\s().-]", "", value)
    if not PHONE_PATTERN.fullmatch(normalized):
        raise serializers.ValidationError(
            "Enter a phone number with 7 to 15 digits, optionally prefixed by +."
        )
    return normalized


class RegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        min_length=8,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate_email(self, value):
        email = value.strip().lower()
        if (
            User.objects.filter(email__iexact=email).exists()
            or CustomerProfile.objects.filter(email__iexact=email).exists()
        ):
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return email

    def validate_phone_number(self, value):
        return normalize_phone_number(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The passwords do not match."}
            )

        candidate = User(
            username=f"fb_{uuid.uuid4().hex}",
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
            email=attrs["email"],
        )
        try:
            password_validation.validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"password": list(error.messages)}
            ) from error
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        phone_number = validated_data.pop("phone_number")
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=f"fb_{uuid.uuid4().hex}",
                    password=password,
                    **validated_data,
                )
                return CustomerProfile.objects.create(
                    user=user,
                    email=validated_data["email"],
                    phone_number=phone_number,
                )
        except IntegrityError as error:
            raise serializers.ValidationError(
                {"email": "An account with this email already exists."}
            ) from error


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        users = list(User.objects.filter(email__iexact=email)[:2])
        if len(users) != 1:
            raise AuthenticationFailed("Invalid email or password.")

        user = authenticate(
            request=self.context.get("request"),
            username=users[0].get_username(),
            password=attrs["password"],
        )
        if user is None:
            raise AuthenticationFailed("Invalid email or password.")

        try:
            profile = user.customer_profile
        except CustomerProfile.DoesNotExist:
            try:
                with transaction.atomic():
                    profile = CustomerProfile.objects.create(
                        user=user,
                        email=user.email.strip().lower(),
                    )
            except IntegrityError as error:
                raise AuthenticationFailed("Invalid email or password.") from error

        return {"user": user, "profile": profile}


class CustomerProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        source="user.first_name",
        max_length=150,
        required=False,
    )
    last_name = serializers.CharField(
        source="user.last_name",
        max_length=150,
        required=False,
    )
    email = serializers.EmailField(max_length=254)
    phone_number = serializers.CharField(max_length=20, required=False)

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_email(self, value):
        email = value.strip().lower()
        profiles = CustomerProfile.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        )
        users = User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.user_id
        )
        if profiles.exists() or users.exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return email

    def validate_phone_number(self, value):
        return normalize_phone_number(value)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        email = validated_data.pop("email", instance.email)
        phone_number = validated_data.pop("phone_number", instance.phone_number)

        with transaction.atomic():
            instance.email = email
            instance.phone_number = phone_number
            instance.save()

            user = instance.user
            user.email = email
            user.first_name = user_data.get("first_name", user.first_name)
            user.last_name = user_data.get("last_name", user.last_name)
            user.save(update_fields=["email", "first_name", "last_name"])

        return instance


class CustomerAddressSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=20)

    class Meta:
        model = CustomerAddress
        fields = [
            "id",
            "full_name",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "landmark",
            "city",
            "state",
            "postal_code",
            "address_type",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_phone_number(self, value):
        return normalize_phone_number(value)
