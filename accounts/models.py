""" Module contains account models """
from datetime import timedelta
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager
)
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import get_template
from ecommerce.utils import unique_key_generator

DEFAULT_ACTIVATION_DAYS = getattr(settings, 'DEFAULT_ACTIVATION_DAYS', 7)


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
        user_obj.save(using=self._db)
        return user_obj


class User(AbstractBaseUser):
    """Custom user model"""
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
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


class EmailActivationQuerySet(models.query.QuerySet):
    """ Email activation custom queryset """
    def confirmable(self):
        """"""
        now = timezone.now()
        start_range = now - timedelta(days=DEFAULT_ACTIVATION_DAYS)
        end_range = now
        return self.filter(
                    activated=False,
                    forced_expired=False
                    ).filter(
                        timestamp__gt=start_range,
                        timestamp__lte=now
                    )


class EmailActivationManager(models.Manager):
    def get_queryset(self):
        return EmailActivationQuerySet(self.model, using=self._db)

    def confirmable(self):
        return self.get_queryset().confirmable()

    def email_exists(self, email):
        return self.get_queryset().filter(
            Q(email=email) | Q(user__email=email)
            ).filter(
                activated=False
            )


class EmailActivation(models.Model):
    user = models.ForeignKey(User)
    email = models.EmailField()
    key = models.CharField(max_length=120, blank=True, null=True)
    activated = models.BooleanField(default=False)
    forced_expired = models.BooleanField(default=False)
    expires = models.IntegerField(default=7)
    timestamp = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now_add=True)

    objects = EmailActivationManager()

    def __str__(self):
        return self.user.email

    def regenerate(self):
        """ Regenerates activation key """
        self.key = None
        self.save()
        if self.key is not None:
            return True
        return False

    def can_activate(self):
        """Checks whether a given user can be activated or not"""
        qs = EmailActivation.objects.filter(pk=self.pk).confirmable()
        return qs.exists()

    def activate(self):
        """Activate a user account"""
        if self.can_activate():
            user = self.user
            user.is_active = True
            user.save()
            self.activated = True
            self.save()
            return True
        return False

    def send_activation(self):
        """ Sends activation email """
        if not self.activated and not self.forced_expired:
            print(self.key)
            print(self.email)
            if self.key:
                base_url = getattr(settings, 'BASE_URL', '127.0.0.1:8000')
                key_path = reverse("account:email-activate",
                                   kwargs={'key': self.key})
                path = "{base}{path}".format(base=base_url, path=key_path)
                context = {
                    'path': path,
                    'email': self.email
                }
                txt_ = get_template(
                    "accounts/email/verify.txt").render(context)
                html_ = get_template(
                    "accounts/email/verify.html").render(context)
                subject = 'Inno Ecommerce'
                from_email = settings.DEFAULT_FROM_EMAIL
                recepient_list = [self.email]
                sent_mail = send_mail(
                    subject,
                    txt_,
                    from_email,
                    recepient_list,
                    html_message=html_,
                    fail_silently=False,
                )
                return sent_mail
        return False


def pre_save_email_activation(sender, instance, *args, **kwargs):
    """ Auto generates activation key before saving EmailActivation object"""
    if not instance.key:
        instance.key = unique_key_generator(instance)


def post_save_user_create_receiver(sender, instance, created, *args, **kwargs):
    """ Sends Activation email after creating a user """
    if created:
        obj = EmailActivation.objects.create(
            user=instance, email=instance.email)
        obj.send_activation()

pre_save.connect(pre_save_email_activation, sender=EmailActivation)
post_save.connect(post_save_user_create_receiver, sender=User)


class Profile(models.Model):
    """ Model for the Merchant Profile """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True, null=True)
    merchant = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email

    def is_merchant(self):
        return self.merchant


def post_save_user_receiver(sender, instance, *args, **kwargs):
    """ Creates a user profile after saving a user object """
    if not instance.profile_set.first():
        instance.profile_set.create()

post_save.connect(post_save_user_receiver, sender=User)
