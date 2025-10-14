from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinLengthValidator

# -----------------------------
# User Manager
# -----------------------------
class UserManager(BaseUserManager):
    def create_user(self, username, email, first_name=None, last_name=None,
                    phone=None, user_type="Persona Fisica", password=None):
        if not email:
            raise TypeError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.first_name = first_name
        user.last_name = last_name
        user.user_type = user_type
        user.username = username
        user.phone = phone
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        if not password:
            raise TypeError("Password is required for superuser")
        user = self.create_user(username, email, None, None, None, "Persona Fisica", password)
        user.is_superuser = True
        user.is_staff = True
        user.permission = 100
        user.is_verified = True
        user.save(using=self._db)
        return user


# -----------------------------
# Enums / choices
# -----------------------------
USER_LEVEL = (
    (100, "SuperAdmin"),
    (50, "Admin"),
    (10, "Utente"),
    (5, "Employee"),
)

USER_TYPE_CHOICES = (
    ("Persona Fisica", "Persona Fisica"),
    ("Azienda", "Azienda"),
    ("NoProfit", "Ente No Profit"),
)

def user_directory_path(instance, filename):
    return f'avatars/user_{instance.id}/{filename}'

# -----------------------------
# User model
# -----------------------------
class User(AbstractBaseUser, PermissionsMixin):
    # Base information
    username = models.CharField(max_length=40, validators=[MinLengthValidator(4)], null=True, blank=True)
    email = models.CharField(max_length=70, validators=[MinLengthValidator(4)], unique=True, db_index=True)

    # System flags
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Permissions
    permission = models.PositiveSmallIntegerField(verbose_name="User permission level",
                                                  default=1, choices=USER_LEVEL)
    user_type = models.CharField(max_length=30, choices=USER_TYPE_CHOICES, default="Persona Fisica")

    # Profile fields
    first_name = models.CharField(verbose_name="Nome", max_length=50, blank=True, null=True)
    last_name = models.CharField(verbose_name="Cognome", max_length=50, blank=True, null=True)
    fiscal_code = models.CharField(verbose_name="Codice Fiscale", max_length=16, blank=True, null=True)
    phone = models.CharField(verbose_name="Telefono", max_length=12, blank=True, null=True)
    mobile = models.CharField(verbose_name="Cellulare", max_length=12, blank=True, null=True)
    avatar = models.ImageField(upload_to=user_directory_path, blank=True, null=True)

    # Django auth fields
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.email

    # Utils
    def is_superadmin(self):
        return self.permission == 100

    def is_admin(self):
        return self.permission == 50
    
    def is_user(self):
        return self.permission == 1

    def is_associate(self):
        return True if self.permission == 50 else False

    def is_partner(self):
        return True if self.permission == 2 else False

    def is_client(self):
        return True if self.permission == 1 else False

    def is_at_least_partner(self):
        return True if self.permission > 1 else False

    def is_at_least_associate(self):
        return True if self.permission > 49 else False
    
    def get_type(self):
        return self.user_type

    def get_name(self):
        first = self.first_name or ""
        last = self.last_name or ""
        return (first + " " + last).strip()

    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
        ordering = ("last_name",)
