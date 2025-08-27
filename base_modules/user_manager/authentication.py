import datetime
import jwt
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from django.conf import settings
from .models import User

# NOTE:
# - This authentication is used when AUTH_MODE=django
# - It expects "Authorization: Bearer <token>" (or any two-part auth header)

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if auth and len(auth) == 2:
            token = auth[1].decode("utf-8")
            user_id = decode_access_token(token)
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed("user not found")
            return (user, None)
        raise exceptions.AuthenticationFailed("unauthenticated #001")

def _jwt_secret():
    return getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)

def create_access_token(user_id, permission, user_type):
    return jwt.encode(
        {
            "user_id": user_id,
            "permission": permission,
            "user_type": user_type,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8),
            "iat": datetime.datetime.utcnow(),
        },
        _jwt_secret(),
        algorithm="HS256",
    )

def decode_access_token(token):
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
        return payload["user_id"]
    except Exception:
        raise exceptions.AuthenticationFailed("unauthenticated")

def create_refresh_token(user_id):
    return jwt.encode(
        {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=5),
            "iat": datetime.datetime.utcnow(),
        },
        _jwt_secret(),
        algorithm="HS256",
    )

def decode_refresh_token(token):
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
        return payload["user_id"]
    except Exception:
        raise exceptions.AuthenticationFailed("unauthenticated")
