from django.contrib import auth
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from .models import User

# -----------------------------
# Register
# -----------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=8, write_only=True, required=True)
    password_confirm = serializers.CharField(max_length=68, min_length=8, write_only=True, required=True)
    initial_prompt = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password", "password_confirm", "initial_prompt")

        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        initial_prompt = validated_data.pop("initial_prompt", None)

        # Use email as username
        validated_data["username"] = validated_data["email"]
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        return user


# -----------------------------
# Login (data carrier)
# -----------------------------
class UserSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=250, min_length=3)
    password = serializers.CharField(max_length=255, min_length=4, write_only=True)
    tokens = serializers.CharField(max_length=255, min_length=4, read_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "tokens"]

    def validate(self, attrs):
        email = attrs.get("email", "")
        password = attrs.get("password", "")

        user = auth.authenticate(email=email, password=password)
        if not user:
            return {"id_user": "", "permission": "", "email": "", "tokens": ""}

        return {
            "id_user": user.id,
            "permission": user.permission,
            "email": user.email,
            "tokens": user.tokens,  # only if you implement this property elsewhere
        }


class RequestResetPWMail(serializers.ModelSerializer):
    email = serializers.CharField(max_length=250, min_length=3)

    class Meta:
        model = User
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email", "")
        try:
            user = User.objects.get(email=email)
            # Here you would actually send an email; we keep it stubbed.
            return {"sending": "success"}
        except User.DoesNotExist:
            return {"sending": "failed"}
        except User.MultipleObjectsReturned:
            return {"sending": "failed"}


class RequestResetPW(serializers.ModelSerializer):
    password = serializers.CharField(max_length=255, min_length=4, write_only=True)
    password_confirm = serializers.CharField(max_length=255, min_length=4, write_only=True)

    class Meta:
        model = User
        fields = ["password", "password_confirm"]


# -----------------------------
# User details
# -----------------------------
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "fiscal_code",
            "phone",
            "mobile",
            "avatar",
            "permission",
        ]


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "password"]


class GetMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]
