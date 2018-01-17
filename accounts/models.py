""" Module contains account models """
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager
)


class UserManager(BaseUserManager):
    """ Model manager for our custom user model"""
    def create_user(self, email, password=None):
        """Creates and saves a new user with the given email and password"""
        if not email:
            raise ValueError("Users must have an email")
        if not password:
            raise ValueError("User must have a password")

        user_obj = self.model(
            email=self.normalize_email(email)
        )

        user_obj.set_password(password)
        user_obj.save(using=self._db)
        return user_obj

    def create_staffuser(self, email, password):
        """ Creates and saves a staff user """
        user_obj = self.create_user(email, password=password)
        user_obj.staff = True
        user_obj.save(using=self._db)
        return user_obj

    def create_superuser(self, email, password):
        """ Create and save a super user """
        user_obj = self.create_user(email, password=password)
        user_obj.staff = True
        user_obj.admin = True
        user_obj.active = True
        user_obj.save(using=self._db)
        return user_obj


class User(AbstractBaseUser):
    """Custom user model"""
    email = models.EmailField(max_length=255, unique=True)
    active = models.BooleanField(default=False)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_full_name(self):
        """" User is identified by their email address"""
        return self.email

    def get_short_name(self):
        """" User is identified by their email address"""
        return self.email

    def has_perm(self, perm, obj=None):
        """ Does the user have a specific permission"""
        return True
    
    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app 'app_label' """
        return True

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        """ Is the user an administrator """
        return self.admin

    @property
    def is_staff(self):
        """ Is the user a member of staff """
        return self.staff

    @property
    def is_active(self):
        """ Is the user account active """
        return self.active


class Profile(models.Model):
    """ Model for the Merchant Profile """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True, null=True)
    merchant = models.BooleanField(default=False)

    def __str__(self):
        return self.shop

    def is_merchant(self):
        return self.merchant



def profile_post_save_receiver(sender, instance, *args, **kwargs):
    if not instance.profile_set.first():
        instance.profile_set.create()


post_save.connect(profile_post_save_receiver, sender=User)
