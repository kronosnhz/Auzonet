from __future__ import unicode_literals

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

GENDERS = (
    ('M', 'Male'),
    ('F', 'Female')
)
ACCESS_TYPE = (
    ('PU', 'Public'),
    ('PR', 'Private'),
)
ORDER_TYPES = (
    ('O', 'Offer'),
    ('R', 'Request'),
)
STATUS = (
    ('A', 'Active'),
    ('P', 'Pending'),
    ('F', 'Finished'),
)

SCOPE = (
    ('COM', 'Community'),
    ('CIT', 'City'),
    ('PRO', 'Province'),
)
MESSAGE_TYPES = (
    ('I', 'Info'),
    ('W', 'Warning'),
)


class Community(models.Model):
    class Meta:
        verbose_name_plural = "Communities"

    access_type = models.CharField(max_length=2, choices=ACCESS_TYPE, default='PU')
    address = models.CharField(max_length=250)
    coordinates = models.CharField(max_length=250)
    password = models.CharField(blank=True, max_length=250)
    welcome_message = models.TextField()

    def __unicode__(self):
        return self.address


class Category(models.Model):
    class Meta:
        verbose_name_plural = "Categories"

    title = models.CharField(max_length=250)
    description = models.TextField()

    def __unicode__(self):
        return self.title


class Request(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requested_by")
    title = models.CharField(max_length=250)
    detail = models.TextField()
    date_published = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    scope = models.CharField(max_length=3, choices=SCOPE, default='COM')
    status = models.CharField(max_length=1, choices=STATUS, default='A')
    reward = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10, default=0, help_text="EUR. Leave it blank for no reward.", validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(blank=True, upload_to='uploads/requests/%Y/%m/%d/')

    def __unicode__(self):
        return self.title + " created on " + str(self.date_published)


class Offer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offered_by")
    title = models.CharField(max_length=250)
    detail = models.TextField()
    date_published = models.DateTimeField(auto_now_add=True)
    scope = models.CharField(max_length=3, choices=SCOPE, default='COM')
    status = models.CharField(max_length=1, choices=STATUS, default='A')
    price = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10, default=0, help_text="EUR. Leave it blank for no price.", validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(blank=True, upload_to='uploads/offers/%Y/%m/%d/')

    def __unicode__(self):
        return self.title + " created on " + str(self.date_published)


class Order(models.Model):
    order_type = models.CharField(max_length=1, choices=ORDER_TYPES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="server")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client")
    offer = models.ForeignKey(Offer, blank=True, null=True, on_delete=models.CASCADE)
    auzonetrequest = models.ForeignKey(Request, blank=True, null=True, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    owner_voted = models.BooleanField(blank=True, default=False)
    client_voted = models.BooleanField(blank=True, default=False)
    status = models.CharField(max_length=1, choices=STATUS, default='A')

    def __unicode__(self):
        return "Client: " + self.client.username + " Owner: " + self.owner.username + " Type: " + self.order_type + " Created on: " + str(
            self.date_created)


# fist_name, last_name, email, password belongs to superclass User
class PublicUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    communities = models.ManyToManyField(Community)
    birthdate = models.DateField(null=True)
    gender = models.CharField(max_length=1, choices=GENDERS, default='M')
    karma = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='uploads/avatars/%Y/%m/%d/')

    def __unicode__(self):
        return self.user.username

    """ IMAGE PROCESSING ON DEVELOPMENT
    def save(self):
        factor = 1
        if not self.id and not self.photo:
            return

        super(PublicUser, self).save()

        userPhoto = Image.open(self.photo)
        (width, height) = userPhoto.size
        print(str(userPhoto.size))
        "Max width and height 800"
        if (800 / width < 800 / height):
            factor = 800 / height
        else:
            factor = 800 / width

        size = ( width / factor, height / factor)
        userPhoto = userPhoto.resize(size, Image.ANTIALIAS)
        userPhoto.save(self.photo.path)

        if not self.id and not self.avatar:
            return

        super(PublicUser, self).save()

        userAvatar = Image.open(self.avatar)
        (width, height) = userAvatar.size

        "Max width and height 800"
        if (800 / width < 800 / height):
            factor = 800 / height
        else:
            factor = 800 / width

        size = ( width / factor, height / factor)
        userAvatar = userAvatar.resize(size, Image.ANTIALIAS)
        userAvatar.save(self.avatar.path)
        """


class CommunityMessage(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=1, choices=MESSAGE_TYPES, default='I')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_by")
    date_published = models.DateTimeField(auto_now_add=True)
    message_text = models.TextField()

    def __unicode__(self):
        return self.message_type + " created on " + str(self.date_published)
