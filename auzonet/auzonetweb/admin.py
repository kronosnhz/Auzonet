from django.contrib import admin

# Register your models here.
from .models import Community, PublicUser, Category, Request, Offer, CommunityMessage, Order

myModels = {Community, PublicUser, Category, Request, Offer, CommunityMessage, Order}

admin.site.register(myModels)
