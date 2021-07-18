import datetime
from django.db import models
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
import stripe
from django.utils import timezone
# Create your models here.
stripe.api_key = "sk_test_51Ix7DoSDH8LbnqpkT3MyKegLDXZWeBvwsCdrX5HyLpcbLxWfxCBRkA0TF1JUb1kezcDIHc26TC7DLQhpk9yQPudT00zZIB8J8w"

MEMBERSHIP_CHOICES = (
    ('F', 'free_trial'),
    ('M', 'member'),
    ('N', 'not_member'),
)


class File(models.Model):
    file = models.ImageField()

    def __str__(self):
        return self.file.name


class User(AbstractUser):
    is_member = models.BooleanField(default=False)
    on_free_trial = models.BooleanField(default=True)
    stripe_customer_id = models.CharField(max_length=40)


class Address(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    line1 = models.CharField(max_length=256)
    postal_code = models.CharField(max_length=7)
    city = models.CharField(max_length=256)
    state = models.CharField(max_length=40)
    country = models.CharField(max_length=40)


class Membership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=MEMBERSHIP_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    stripe_subscription_id = models.CharField(
        max_length=40, blank=True, null=True)
    stripe_subscription_item_id = models.CharField(
        max_length=40, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField()

    def __str__(self):
        return self.user.username


class TrackedRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    usage_record_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username


def post_save_user_receiver(sender, instance, created, *args, **kwargs):
    if created:
        import datetime
        # customer = stripe.Customer.create(email=instance.email)
        # instance.stripe_customer_id = customer.id
        # instance.save()

        membership = Membership.objects.get_or_create(
            user=instance,
            type='F',
            start_date=timezone.now(),
            end_date=timezone.now() + datetime.timedelta(days=14)
        )


def user_logged_in_reciever(sender, user, request, **kwargs):
    membership = user.membership

    if user.on_free_trial:
        # membership date has passed
        if membership.end_date < timezone.now():
            user.on_free_trial = False

    elif user.is_member:
        sub = stripe.Subscription.retrieve(membership.stripe_subscription_id)
        if sub.status == "active":
            membership.end_date = datetime.date.fromtimestamp(
                sub.current_period_end
            )
            membership.save()
            user.is_member = True
        else:
            user.is_member = False
    else:
        pass

    user.save()
    membership.save()


post_save.connect(post_save_user_receiver, sender=User)
user_logged_in.connect(user_logged_in_reciever)
