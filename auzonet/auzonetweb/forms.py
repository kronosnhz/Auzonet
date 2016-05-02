from django import forms
from django.forms import ModelForm

from .models import Community, Request, Offer, CommunityMessage

GENDERS = (
    ('M', 'Male'),
    ('F', 'Female')
)

ACCESS_TYPES = (
    ('PU', 'Public'),
    ('PR', 'Private'),
)

SCOPE = (
    ('COM', 'Community'),
    ('CIT', 'City'),
    ('PRO', 'Province'),
    ('COU', 'Country'),
)

STATUS = (
    ('A', 'Active'),
    ('F', 'Finished'),
)


class LoginForm(forms.Form):
    username = forms.CharField(required=True, label='Username', max_length=100)
    password = forms.CharField(required=True, label='Password', max_length=100, widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    username = forms.CharField(required=True, label='Username', max_length=100)
    first_name = forms.CharField(required=True, label='Name', max_length=100)
    last_name = forms.CharField(required=True, label='Surname', max_length=100)
    email = forms.EmailField(required=True, label='Email', max_length=100, widget=forms.EmailInput)
    password = forms.CharField(required=True, label='Password', max_length=100, widget=forms.PasswordInput)
    birthdate = forms.DateField(required=True, label='Birthday')
    gender = forms.ChoiceField(required=True, label='Gender', choices=GENDERS)
    avatar = forms.ImageField(required=True, label='Avatar', max_length=100)


class JoinCommunityForm(forms.Form):
    community = forms.ModelChoiceField(queryset=Community.objects.all())


class ProtectedCommunityForm(forms.Form):
    password = forms.CharField(required=True, label='Password', max_length=100, widget=forms.PasswordInput)


class NewCommunityMsgModelForm(ModelForm):
    class Meta:
        model = CommunityMessage
        fields = ['message_type', 'message_text']
        localized_fields = '__all__'


class NewCommunityForm(forms.Form):
    access_type = forms.ChoiceField(choices=ACCESS_TYPES)
    neighborhood_code = forms.IntegerField(widget=forms.HiddenInput)
    neighborhood_name = forms.CharField(widget=forms.HiddenInput)
    street_code = forms.IntegerField(widget=forms.HiddenInput)
    street_name = forms.CharField(widget=forms.HiddenInput)
    door_code = forms.IntegerField(widget=forms.HiddenInput)
    coordinatesX = forms.DecimalField(widget=forms.HiddenInput)
    coordinatesY = forms.DecimalField(widget=forms.HiddenInput)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    welcome_message = forms.CharField(widget=forms.Textarea, required=False)

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
