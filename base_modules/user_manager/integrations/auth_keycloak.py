import jwt
from jwt import PyJWKClient
from rest_framework import authentication, exceptions
from django.conf import settings
from .models import User

class KeycloakJWTAuthentication(authentication.BaseAuthentication):
    """
    Bearer token validation for Keycloak:
    - Verifies RS256 signature using JWKS
    - Maps/creates a local Django user to keep the rest of the app consistent
    """
    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header or " " not in header:
            return None
        prefix, token = header.split(" ", 1)
        if prefix.lower() != "bearer":
            return None

        jwks_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
        try:
            jwk_client = PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token).key

            # Set verify_aud=True if you want to enforce audience == OIDC_RP_CLIENT_ID
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
                audience=getattr(settings, "OIDC_RP_CLIENT_ID", None),
            )
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Invalid token: {e}")

        email = payload.get("email")
        username = payload.get("preferred_username") or email
        first_name = payload.get("given_name", "")
        last_name = payload.get("family_name", "")

        if not email:
            raise exceptions.AuthenticationFailed("Token missing email")

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username or email,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
            },
        )

        # Optional: map realm roles to permission
        roles = (payload.get("realm_access") or {}).get("roles", [])
        if "superadmin" in roles:
            user.permission = 100
        elif "admin" in roles:
            user.permission = 50
        else:
            user.permission = 1
        user.save(update_fields=["permission"])

        return (user, None)
