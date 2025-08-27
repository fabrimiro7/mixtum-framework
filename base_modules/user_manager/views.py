import re
import datetime
from django.conf import settings
from django.contrib.auth import logout
from rest_framework import status, exceptions
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    RequestResetPWMail, RequestResetPW,
    UserDetailSerializer, UserDetailSerializer,
    GetMembersSerializer
)

# Dynamic auth class switch based on AUTH_MODE
if getattr(settings, "AUTH_MODE", "django") == "keycloak":
    from .auth_keycloak import KeycloakJWTAuthentication as _Auth
else:
    from .authentication import JWTAuthentication as _Auth

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.exceptions import AuthenticationFailed
from .authentication import (
    create_access_token, create_refresh_token, decode_refresh_token
)

# -----------------------------
# Registration
# -----------------------------
class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        user_data = serializer.data

        return Response(
            {"user": user_data, "message": "success", "id_user": user.id},
            status=status.HTTP_200_OK,
        )


# -----------------------------
# Login (local JWT) – disabled in keycloak mode
# -----------------------------
class LoginUserView(CreateAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if getattr(settings, "AUTH_MODE", "django") == "keycloak":
            return Response(
                {"detail": "Use Keycloak login (OIDC) and pass Bearer token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        print("ciao sono quii")
        email = request.data.get("email")
        password = request.data.get("password")

        user = User.objects.filter(email=email).first()
        if user is None:
            raise exceptions.AuthenticationFailed("Invalid credentials")

        if not user.check_password(password):
            raise exceptions.AuthenticationFailed("Invalid credentials")

        access_token = create_access_token(user.id, user.permission, user.user_type)
        refresh_token = create_refresh_token(user.id)

        response = Response()
        response.set_cookie(key="refresh_token_dj", value=refresh_token, httponly=False)
        response.data = {
            "token": access_token,
            "refresh_token": refresh_token,
            "message": "success",
        }
        return response


# -----------------------------
# Refresh token (local JWT) – disabled in keycloak mode
# -----------------------------
class RefreshAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if getattr(settings, "AUTH_MODE", "django") == "keycloak":
            return Response(
                {"detail": "Use Keycloak Bearer tokens; no local refresh."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh_token = request.data.get("reftok") or request.COOKIES.get("refresh_token_dj")
        if not refresh_token or refresh_token == "undefined":
            raise exceptions.AuthenticationFailed("Missing refresh token")

        user_id = decode_refresh_token(refresh_token)
        user = get_object_or_404(User, pk=user_id)
        access_token = create_access_token(user_id, user.permission, user.user_type)
        return Response({"token": access_token})


# -----------------------------
# Password reset (stubs)
# -----------------------------
class RequestResetPasswordMail(APIView):
    serializer_class = RequestResetPWMail

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "success"}, status=status.HTTP_200_OK)


class ResetPassword(APIView):
    serializer_class = RequestResetPW

    def post(self, request, id, token):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = request.data.get("password", "")
        password_confirm = request.data.get("password_confirm", "")
        user = get_object_or_404(User, pk=id)
        token = token.replace("_", "-")

        if not PasswordResetTokenGenerator().check_token(user=user, token=token):
            raise AuthenticationFailed("Token Consumed", 401)
        if password != password_confirm:
            raise AuthenticationFailed("Passwords do not match", 401)

        user.set_password(password)
        user.save()

        return Response({"message": "success"}, status=status.HTTP_200_OK)


# -----------------------------
# Logout
# -----------------------------
class Logout(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request, *args, **kwargs):
        response = Response()
        response.delete_cookie(key="refresh_token")
        logout(request)
        return Response({"message": "success"}, status=status.HTTP_200_OK)


# -----------------------------
# User CRUD / listing (auth required)
# -----------------------------
class UserDetail(APIView):
    serializer_class = UserDetailSerializer
    authentication_classes = [_Auth]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserDetailSerializer(user)
        return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserDetailSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "success"}, status=status.HTTP_200_OK)
        return Response({"data": serializer.errors, "message": "fail"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response({"message": "success"}, status=status.HTTP_204_NO_CONTENT)


class GetMembersAPIView(APIView):
    authentication_classes = [_Auth]
    serializer_class = GetMembersSerializer

    def get(self, request):
        members = User.objects.all()
        serializer = GetMembersSerializer(members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetUserAPIView(APIView):
    serializer_class = UserDetailSerializer
    authentication_classes = [_Auth]

    def get(self, request):
        users = User.objects.all()
        serializer = UserDetailSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserView(CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data.get("email", "")
        if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
            return Response({"user": "", "message": "fail"}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        user_data = serializer.data
        return Response(
            {"user": user_data, "message": "success", "id_user": user.id},
            status=status.HTTP_200_OK,
        )
