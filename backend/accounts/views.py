from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.db import transaction
from django.http import Http404
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accounts.models import CustomerAddress, CustomerProfile
from accounts.serializers import (
    CustomerAddressSerializer,
    CustomerProfileSerializer,
    EmailLoginSerializer,
    RegistrationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

REFRESH_COOKIE_NAME = settings.AUTH_REFRESH_COOKIE_NAME
User = get_user_model()


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            frontend = settings.FRONTEND_URL if hasattr(settings, "FRONTEND_URL") else "http://localhost:5173"
            send_mail(
                "Reset your FreshBasket password",
                f"Open {frontend}/reset-password/{uid}/{token} to choose a new password. This link expires soon.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        return Response({"detail": "If an account exists for that email, reset instructions have been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password reset successfully. You can now sign in."})


def _lock_customer(user):
    User.objects.select_for_update().get(pk=user.pk)


def _owned_address(customer, address_id):
    return get_object_or_404(
        CustomerAddress.objects.filter(customer=customer),
        pk=address_id,
    )


def set_refresh_cookie(response, refresh_token):
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=str(refresh_token),
        max_age=int(lifetime.total_seconds()),
        httponly=True,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
    )


def delete_refresh_cookie(response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )


def token_response(profile, response_status=status.HTTP_200_OK):
    refresh = RefreshToken.for_user(profile.user)
    response = Response(
        {
            "access": str(refresh.access_token),
            "user": CustomerProfileSerializer(profile).data,
        },
        status=response_status,
    )
    set_refresh_cookie(response, refresh)
    return response


@method_decorator(csrf_protect, name="dispatch")
class CsrfTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "csrf_token": get_token(request),
                "refresh_cookie_present": bool(request.COOKIES.get(REFRESH_COOKIE_NAME)),
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return token_response(profile, status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailLoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return token_response(serializer.validated_data["profile"])


@method_decorator(csrf_protect, name="dispatch")
class TokenRefreshCookieView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not refresh_token:
            response = Response(
                {"detail": "Refresh token is missing or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            delete_refresh_cookie(response)
            return response

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            is_valid = serializer.is_valid()
        except TokenError:
            is_valid = False
        if not is_valid:
            response = Response(
                {"detail": "Refresh token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            delete_refresh_cookie(response)
            return response

        data = serializer.validated_data
        access_token = AccessToken(data["access"])
        user_id = access_token.get(jwt_api_settings.USER_ID_CLAIM)
        profile = (
            CustomerProfile.objects.select_related("user")
            .filter(user_id=user_id, user__is_active=True)
            .first()
        )
        if profile is None:
            response = Response(
                {"detail": "Refresh token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            delete_refresh_cookie(response)
            return response

        response_data = {
            "access": data["access"],
            "user": CustomerProfileSerializer(profile).data,
        }
        response = Response(response_data)
        rotated_refresh = data.get("refresh")
        if rotated_refresh:
            set_refresh_cookie(response, rotated_refresh)
        return response


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        response = Response(status=status.HTTP_204_NO_CONTENT)
        delete_refresh_cookie(response)
        return response


class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get_profile(self, request):
        try:
            return request.user.customer_profile
        except CustomerProfile.DoesNotExist as error:
            raise Http404 from error

    def get(self, request):
        profile = self.get_profile(request)
        return Response(CustomerProfileSerializer(profile).data)

    def patch(self, request):
        profile = self.get_profile(request)
        serializer = CustomerProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CustomerAddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = CustomerAddress.objects.filter(customer=request.user)
        return Response(CustomerAddressSerializer(addresses, many=True).data)

    def post(self, request):
        serializer = CustomerAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            _lock_customer(request.user)
            addresses = CustomerAddress.objects.filter(customer=request.user)
            make_default = serializer.validated_data.get("is_default", False)
            if make_default or not addresses.filter(is_default=True).exists():
                addresses.update(is_default=False)
                make_default = True
            address = serializer.save(customer=request.user, is_default=make_default)

        return Response(
            CustomerAddressSerializer(address).data,
            status=status.HTTP_201_CREATED,
        )


class CustomerAddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, address_id):
        address = _owned_address(request.user, address_id)
        return Response(CustomerAddressSerializer(address).data)

    def patch(self, request, address_id):
        with transaction.atomic():
            _lock_customer(request.user)
            address = _owned_address(request.user, address_id)
            serializer = CustomerAddressSerializer(
                address,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)

            make_default = serializer.validated_data.get(
                "is_default",
                address.is_default,
            )
            if make_default:
                CustomerAddress.objects.filter(customer=request.user).exclude(
                    pk=address.pk
                ).update(is_default=False)
            elif address.is_default:
                replacement = (
                    CustomerAddress.objects.filter(customer=request.user)
                    .exclude(pk=address.pk)
                    .order_by("created_at", "pk")
                    .first()
                )
                if replacement:
                    replacement.is_default = True
                    replacement.save(update_fields=["is_default", "updated_at"])
                else:
                    make_default = True

            address = serializer.save(is_default=make_default)

        return Response(CustomerAddressSerializer(address).data)

    def delete(self, request, address_id):
        with transaction.atomic():
            _lock_customer(request.user)
            address = _owned_address(request.user, address_id)
            was_default = address.is_default
            address.delete()
            if was_default:
                replacement = (
                    CustomerAddress.objects.filter(customer=request.user)
                    .order_by("created_at", "pk")
                    .first()
                )
                if replacement:
                    replacement.is_default = True
                    replacement.save(update_fields=["is_default", "updated_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerAddressSetDefaultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, address_id):
        with transaction.atomic():
            _lock_customer(request.user)
            address = _owned_address(request.user, address_id)
            CustomerAddress.objects.filter(customer=request.user).exclude(
                pk=address.pk
            ).update(is_default=False)
            if not address.is_default:
                address.is_default = True
                address.save(update_fields=["is_default", "updated_at"])

        return Response(CustomerAddressSerializer(address).data)
