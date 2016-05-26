from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy

from .models import Community, Request, Offer, CommunityMessage

GENDERS = (
    ('M', ugettext_lazy(u"Male")),
    ('F', ugettext_lazy(u"Female"))
)

ACCESS_TYPES = (
    ('PU', ugettext_lazy(u"Public")),
    ('PR', ugettext_lazy(u"Private")),
)

SCOPE = (
    ('COM', ugettext_lazy(u"Community")),
    ('CIT', ugettext_lazy(u"City")),
    ('PRO', ugettext_lazy(u"Province")),
    ('COU', ugettext_lazy(u"Country")),
)

STATUS = (
    ('A', ugettext_lazy(u"Active")),
    ('F', ugettext_lazy(u"Finished")),
)


class LoginForm(forms.Form):
    username = forms.CharField(required=True, label=ugettext_lazy(u"Username"), max_length=100)
    password = forms.CharField(required=True, label=ugettext_lazy(u"Password"), max_length=100,
                               widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    class Meta:
        localized_fields = '__all__'

    username = forms.CharField(required=True, label=ugettext_lazy(u"Username"), max_length=100,
                               help_text=ugettext_lazy(u"* Required"))
    first_name = forms.CharField(required=True, label=ugettext_lazy(u"Name"), max_length=100,
                                 help_text=ugettext_lazy(u"* Required"))
    last_name = forms.CharField(required=True, label=ugettext_lazy(u"Surname"), max_length=100,
                                help_text=ugettext_lazy(u"* Required"))
    email = forms.EmailField(required=True, label=ugettext_lazy(u"Email"), max_length=100, widget=forms.EmailInput,
                             help_text=ugettext_lazy(u"* Required"))
    password = forms.CharField(required=True, label=ugettext_lazy(u"Password"), max_length=100,
                               widget=forms.PasswordInput,
                               help_text=ugettext_lazy(u"* Required"))
    birthdate = forms.DateField(required=True, label=ugettext_lazy(u"Birthday"), help_text=ugettext_lazy(u"* Required"))
    gender = forms.ChoiceField(required=True, label=ugettext_lazy(u"Gender"), choices=GENDERS,
                               help_text=ugettext_lazy(u"* Required"))
    avatar = forms.ImageField(required=True, label=ugettext_lazy(u"Avatar"), max_length=100,
                              help_text=ugettext_lazy(u"* Required. Will be your public image in the community."))


class JoinCommunityForm(forms.Form):
    community = forms.ModelChoiceField(queryset=Community.objects.all())


class ProtectedCommunityForm(forms.Form):
    password = forms.CharField(required=True, label=ugettext_lazy(u"Password"), max_length=100,
                               widget=forms.PasswordInput)


class NewCommunityMsgModelForm(ModelForm):
    class Meta:
        model = CommunityMessage
        fields = ['message_type', 'message_text']
        localized_fields = '__all__'


class NewCommunityForm(forms.Form):
    access_type = forms.ChoiceField(label=ugettext_lazy(u"Tipo de acceso"), choices=ACCESS_TYPES)
    neighborhood_code = forms.IntegerField(widget=forms.HiddenInput)
    neighborhood_name = forms.CharField(widget=forms.HiddenInput)
    street_code = forms.IntegerField(widget=forms.HiddenInput)
    street_name = forms.CharField(widget=forms.HiddenInput)
    door_code = forms.IntegerField(widget=forms.HiddenInput)
    coordinatesX = forms.DecimalField(widget=forms.HiddenInput)
    coordinatesY = forms.DecimalField(widget=forms.HiddenInput)
    password = forms.CharField(label=ugettext_lazy(u"Password"), widget=forms.PasswordInput, required=False)
    welcome_message = forms.CharField(label=ugettext_lazy(u"Mensaje de bienvenida"), widget=forms.Textarea, required=False)

    class Meta:
        localized_fields = '__all__'


class NewOfferModelForm(ModelForm):
    class Meta:
        model = Offer
        localized_fields = '__all__'
        fields = ['category', 'title', 'detail', 'price', 'image']


class NewRequestModelForm(ModelForm):
    class Meta:
        model = Request
        localized_fields = '__all__'
        fields = ['category', 'title', 'detail', 'due_date', 'reward', 'image']
