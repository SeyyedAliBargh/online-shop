from django.db import models
from django.contrib.auth.models import BaseUserManager, PermissionsMixin, AbstractBaseUser
import django_jalali.db.models as jmodels


class ShopUserManager(BaseUserManager):
    """
    Custom user manager that provides `create_user` and `create_superuser`
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a new `User` instance.
        :param email:
        :param password:
        :param extra_fields:
        :return: user instance
        """
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves a new `User` instance with superuser privileges.
        :param email:
        :param password:
        :param extra_fields:
        :return:
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)



class ShopUser(AbstractBaseUser, PermissionsMixin):
    """
    creating the User model
    """
    email = models.EmailField(max_length=255, unique=True, verbose_name='email')
    phone = models.CharField(max_length=11, unique=True, verbose_name='phone')
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    is_staff = models.BooleanField(default=False, verbose_name='staff status')
    is_superuser = models.BooleanField(default=False, verbose_name='superuser status')
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    # Custom manager for handling user creation and authentication logic
    objects = ShopUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["phone"]

    def __str__(self):
        return self.email

class Profile(models.Model):
    """
    Each User has a Profile containing personal information such as name,
    birthdate, and profile image.
    """
    user = models.OneToOneField(ShopUser, on_delete=models.CASCADE, verbose_name='user', related_name='profile')
    first_name = models.CharField(max_length=250, verbose_name='first name')
    last_name = models.CharField(null=True, blank=True, max_length=250, verbose_name='last name')
    birth_date = jmodels.jDateField(null=True, blank=True, verbose_name='birth date')
    image = models.ImageField(upload_to="profile_image", null=True, blank=True, verbose_name='profile image')
    def __str__(self):
        return self.user.email