from __future__ import unicode_literals

from PIL import Image
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext, ugettext_lazy

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
    ('I', ugettext_lazy(u'Info')),
    ('W', ugettext_lazy(u'Warning')),
)


class Community(models.Model):
    class Meta:
        verbose_name_plural = "Communities"

    access_type = models.CharField(ugettext_lazy(u'Tipo de acceso'), max_length=2, choices=ACCESS_TYPE, default='PU',
                                   help_text=ugettext_lazy(u"You can protect with password the community access."))
    neighborhood_code = models.IntegerField()
    neighborhood_name = models.CharField(max_length=250)
    street_code = models.IntegerField()
    street_name = models.CharField(max_length=250)
    door_code = models.IntegerField()
    coordinatesX = models.DecimalField(decimal_places=2, max_digits=10, default=0, blank=True, null=True)
    coordinatesY = models.DecimalField(decimal_places=2, max_digits=10, default=0, blank=True, null=True)
    password = models.CharField(ugettext_lazy(u'Password'), blank=True, max_length=250)
    welcome_message = models.TextField(ugettext_lazy(u'Mensaje de bienvenida'), help_text=ugettext_lazy(u"This text will be sent to new users in your community."), )

    def __unicode__(self):
        return self.neighborhood_name + ', ' + self.street_name + ', ' + str(self.door_code)


class Category(models.Model):
    class Meta:
        verbose_name_plural = "Categories"

    title = models.CharField(max_length=250)
    description = models.TextField()

    def __unicode__(self):
        return self.title


class Request(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=ugettext_lazy(u'Category'))
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requested_by")
    title = models.CharField(ugettext_lazy(u'Title'), max_length=250)
    detail = models.TextField(ugettext_lazy(u'Detail'))
    date_published = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(ugettext_lazy(u'Due date'), blank=True, null=True)
    scope = models.CharField(max_length=3, choices=SCOPE, default='COM')
    status = models.CharField(max_length=1, choices=STATUS, default='A')
    reward = models.DecimalField(ugettext(u'Reward'), blank=True, null=True, decimal_places=2, max_digits=10, default=0,
                                 help_text=ugettext_lazy(u"EUR. Leave it blank for no reward."))
    image = models.ImageField(ugettext_lazy(u'Image'), blank=True, upload_to='uploads/requests/%Y/%m/%d/')

    def __unicode__(self):
        return self.title + " created on " + str(self.date_published)

    def get_source_filename(self):
        return str(self.image.file)

    def save(self, size=(1000, 500)):
        """
        Save Photo after ensuring it is not blank.  Resize as needed.
        """

        if not self.id and not self.image:
            return

        super(Request, self).save()

        filename = self.get_source_filename()
        image = Image.open(filename)

        image.thumbnail(size, Image.ANTIALIAS)
        image.save(filename)


class Offer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=ugettext_lazy(u'Category'))
    community = models.ForeignKey(Community, on_delete=models.CASCADE, verbose_name=ugettext_lazy(u'Community'))
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offered_by")
    title = models.CharField(ugettext_lazy(u'Title'), max_length=250)
    detail = models.TextField(ugettext_lazy(u'Detail'))
    date_published = models.DateTimeField(auto_now_add=True)
    scope = models.CharField(max_length=3, choices=SCOPE, default='COM')
    status = models.CharField(max_length=1, choices=STATUS, default='A')
    price = models.DecimalField(ugettext_lazy(u'Price'), blank=True, null=True, decimal_places=2, max_digits=10, default=0,
                                help_text=ugettext_lazy(u"EUR. Leave it blank for no price."))
    image = models.ImageField(ugettext_lazy(u'Image'), blank=True, upload_to='uploads/offers/%Y/%m/%d/')

    def __unicode__(self):
        return self.title + " created on " + str(self.date_published)

    def get_source_filename(self):
        return str(self.image.file)

    def save(self, size=(1000, 500)):
        """
        Save Photo after ensuring it is not blank.  Resize as needed.
        """

        if not self.id and not self.image:
            return

        super(Offer, self).save()

        filename = self.get_source_filename()
        image = Image.open(filename)

        image.thumbnail(size, Image.ANTIALIAS)
        image.save(filename)


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
    gender = models.CharField(max_length=1, choices=GENDERS)
    karma = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='uploads/avatars/%Y/%m/%d/')

    def __unicode__(self):
        return self.user.username

    def get_source_filename(self):
        return str(self.avatar.file)
    
    def save(self, size=(500, 300)):
        """
        Save Photo after ensuring it is not blank.  Resize as needed.
        """

        if not self.id and not self.avatar:
            return

        super(PublicUser, self).save()

        filename = self.get_source_filename()
        image = Image.open(filename)

        image.thumbnail(size, Image.ANTIALIAS)
        image.save(filename)

class CommunityMessage(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    message_type = models.CharField(ugettext_lazy(u'Message type'), max_length=1, choices=MESSAGE_TYPES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_by")
    date_published = models.DateTimeField(auto_now_add=True)
    message_text = models.TextField(ugettext_lazy(u'Texto'))

    def __unicode__(self):
        return self.message_type + " created on " + str(self.date_published)
