from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Community, User, PublicUser, Request, Offer, Category, CommunityMessage, Order
from .forms import LoginForm, RegisterForm, NewCommunityModelForm, NewRequestModelForm, JoinCommunityForm, NewOfferModelForm, NewCommunityMsgModelForm
from django.forms import modelformset_factory
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse
import requests

## Here is where the POST and GET request are processed
## Auth API docs https://docs.djangoproject.com/en/1.9/topics/auth/default/
## Customizing the authentication on Django https://docs.djangoproject.com/en/1.9/topics/auth/customizing/

OFFER_TYPE = 'O'
REQUEST_TYPE = 'R'
KARMA_REWARD = 10

# COMMON PLACES
@login_required
def index(request, comid=None):

    if comid != None:
        request.session['currentCommunityId'] = comid
        request.session['currentCommunityAddress'] = Community.objects.get(id=comid).address
    else:
        request.session['currentCommunityId'] = request.user.publicuser.communities.all()[0].id
        request.session['currentCommunityAddress'] = request.user.publicuser.communities.all()[0].address

    offers = Offer.objects.filter(community=request.session['currentCommunityId']).exclude(status='F').order_by('-date_published')
    requests = Request.objects.filter(community=request.session['currentCommunityId']).exclude(status='F').order_by('-date_published')

    myRequests = Request.objects.filter(owner=request.user).exclude(status='F').order_by('-date_published')
    myOffers = Offer.objects.filter(owner=request.user).exclude(status='F').order_by('-date_published')
    communityMessages = CommunityMessage.objects.filter(community=request.session['currentCommunityId']).order_by('-date_published')

    myOrders = Order.objects.filter(client=request.user).exclude(status='F')

    if request.method == 'POST':
        # Form with filled data
        messageModelForm = NewCommunityMsgModelForm(request.POST)
        newMessage = messageModelForm.save(commit=False)
        newMessage.community = Community.objects.get(id=request.session['currentCommunityId'])
        newMessage.owner = request.user
        newMessage.save()

        return redirect('index')
    else:
        messageModelForm = NewCommunityMsgModelForm()

    return render(request, 'auzonetweb/index.html', {
    'offers': offers,
    'requests': requests,
    'myRequests': myRequests,
    'myOrders': myOrders,
    'myOffers':myOffers,
    'communityMessages': communityMessages,
    'messageModelForm': messageModelForm
    })

@login_required
def user_profile(request, userid=None):
    if userid:
        currentUser = User.objects.get(id=userid)
        return render(request, 'auzonetweb/user-profile.html', {'currentUser':currentUser})
    else:
        return render(request, 'auzonetweb/user-profile.html', {'currentUser':request.user})

@login_required
def delete_post(request, postid, posttype):
    if posttype == 'R':
        p = Request.objects.get(id=postid)
    elif posttype == 'O':
        p = Offer.objects.get(id=postid)

    p.status = 'F'
    p.save()
    return redirect('index')

@login_required
def delete_message(request, messageid):
    message = CommunityMessage.objects.get(id=messageid)
    if message.owner.id == request.user.id:
        message.delete()

    return redirect('index')

@login_required
def confirmation_success(request):
    return render(request, 'auzonetweb/confirmation-success.html')

@login_required
def wizard(request):

    communities = Community.objects.all()

    if request.method == 'POST':
        if request.POST['formName'] == 'joinCommunity':
            selectCommunityForm = JoinCommunityForm(request.POST)
            selectedCommunity = Community.objects.get(id=request.POST['community'])
            if selectCommunityForm.is_valid():
                currentUser = User.objects.get(id=request.user.id)
                currentUser.publicuser.communities.add(selectedCommunity)
                currentUser.save()
                request.session['currentCommunityId'] = selectedCommunity.id
                request.session['currentCommunityAddress'] = selectedCommunity.address
                return redirect('index')
        elif request.POST['formName'] == 'newCommunity':
            newCommunityModelForm = NewCommunityModelForm(request.POST)
            if newCommunityModelForm.is_valid():
                newCommunity = newCommunityModelForm.save()

                currentUser = User.objects.get(id=request.user.id)
                currentUser.publicuser.communities.add(newCommunity)
                currentUser.save()
                request.session['currentCommunityId'] = newCommunity.id
                request.session['currentCommunityAddress'] = newCommunity.address

                return redirect('index')
            else:
                return redirect('logout')
    else:
        newCommunityModelForm = NewCommunityModelForm()
        selectCommunityForm = JoinCommunityForm()

    return render(request, 'auzonetweb/wizard.html', {'newCommunityForm':newCommunityModelForm,'selectCommunityForm': selectCommunityForm, 'communities': communities})

def welcome(request):
    if request.user.is_authenticated():
        return redirect('index')
    else:
        # if this is a POST request we need to process the form data
        if request.method == 'POST':
            loginForm = LoginForm(request.POST)
            registerForm = RegisterForm(request.POST, request.FILES)
            if request.POST['formtype'] == 'login':
                # check whether it's valid:
                if loginForm.is_valid():
                    # process the data in form.cleaned_data as required
                    username = request.POST['username']
                    password = request.POST['password']
                    user = authenticate(username=username, password=password)
                    if user is not None:
                        if user.is_active:
                            login(request, user)
                            request.session['currentCommunityId'] = request.user.publicuser.communities.all()[0].id
                            request.session['currentCommunityAddress'] = request.user.publicuser.communities.all()[0].address
                            # Redirect to a success page.
                            return redirect('indexcommunity', comid=request.user.publicuser.communities.all()[0].id)
                        else:
                            # Return a 'disabled account' error message
                            return redirect('welcome')
                    else:
                        # Return an 'invalid login' error message.
                        return redirect('welcome')
            elif request.POST['formtype'] == 'register':
                # check whether it's valid:
                if registerForm.is_valid():
                    # process the data in form.cleaned_data as required
                    username = request.POST['username']
                    password = request.POST['password']
                    email = request.POST['email']
                    first_name = request.POST['first_name']
                    last_name = request.POST['last_name']
                    password = request.POST['password']
                    birthdate = request.POST['birthdate']
                    avatar = request.FILES['avatar']

                    user = User.objects.create_user(username, email, password)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()

                    public = PublicUser()
                    public.user = user
                    public.save()

                    user.publicuser = public
                    user.publicuser.birthdate = birthdate
                    user.publicuser.avatar = avatar
                    user.publicuser.save()
                    user.save()

                    user = authenticate(username=username, password=password)
                    login(request, user)

                    return redirect('wizard')
        else:
            loginForm = LoginForm()
            registerForm = RegisterForm()

        return render(request, 'auzonetweb/welcome.html', {'loginForm': loginForm, 'registerForm':registerForm})

def bootcamp(request):
    datasets = requests.get('https://dev.welive.eu/dev/api/ods/dataset/all', verify=False)
    datasetsjson = datasets.json()
    return render(request, 'auzonetweb/bootcamp.html')

def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return redirect('welcome')

# OFFERS
@login_required
def edit_offer(request, offerid=None):
    if request.method == 'POST':
        # Form with filled data
        if offerid:
            currentOffer = Offer.objects.get(id=offerid)
            offerForm = NewOfferModelForm(request.POST,request.FILES, instance=currentOffer)
        else:
            offerForm = NewOfferModelForm(request.POST, request.FILES)

        newOffer = offerForm.save(commit=False)
        newOffer.community = Community.objects.get(id=request.session['currentCommunityId'])
        newOffer.owner = request.user
        newOffer.save()

        return redirect('index')
    elif offerid!=None:
        # Form for edition
        ap = Offer.objects.get(id=offerid)
        offerForm = NewOfferModelForm(instance=ap)
    else:
        # Empty form
        offerForm = NewOfferModelForm()

    return render(request, 'auzonetweb/offer.html', {'offerForm': offerForm})

@login_required
def detail_offer(request, offerid):
    offer = Offer.objects.get(id=offerid)
    orders = Order.objects.filter(offer=offer).exclude(status='F')

    is_client = 0
    client_order = None
    for o in orders:
        if o.client == request.user:
            is_client = 1
            client_order = o

    return render(request, 'auzonetweb/detail-offer.html', {'offer': offer, 'orders': orders, 'is_client':is_client, 'client_order':client_order})

@login_required
def accept_offer(request, offerid, interestedid):
    userOwner = request.user
    userInterested = User.objects.get(id=interestedid)
    offer = Offer.objects.get(id=offerid)

    if request.user == offer.owner:
        # The logged user is the owner
        order = Order()
        order.order_type = OFFER_TYPE
        order.owner = userOwner
        order.client = userInterested
        order.offer = offer
        order.status = 'A'
        order.save()

        return redirect('confirmation-success')
    else:
        # The logged user is not the owner
        return HttpResponse('You have to be the owner of the offer for accept.')

@login_required
def hire_offer(request, offerid):
    offer = Offer.objects.get(id=offerid)
    userOwner = offer.owner
    userInterested = request.user
    # Email notification
    subject = userInterested.username+" ha solicitado contratar tus servicios"
    html_message = userInterested.username+" esta interesado en tu oferta "+offer.title+". Pulsa <a href="+reverse('accept-offer', kwargs={'offerid':offer.id, 'interestedid':userInterested.id})+">aqui</a> para aceptar su solicitud."
    from_email = userInterested.email
    if subject and html_message and from_email:
        try:
            send_mail(subject, html_message, from_email, [offer.owner.email])
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return redirect('index')
    else:
        # In reality we'd use a form class
        # to get proper validation errors.
        return HttpResponse('Make sure all fields are entered and valid.')

@login_required
def finalize_order(request, orderid, feedback):
    order = Order.objects.get(id=orderid)
    if order.client == request.user:
        # The client is finalizing the order
        if feedback == 1:
            order.owner.publicuser.karma+=KARMA_REWARD
        else:
            order.owner.publicuser.karma-=KARMA_REWARD
        order.status = 'F'
        order.owner.save()
        order.save()
        return redirect('index')
    elif order.owner == request.user:
        # The server is finalizing the order
        if feedback == 1:
            order.client.publicuser.karma+=KARMA_REWARD
        else:
            order.client.publicuser.karma-=KARMA_REWARD
        order.status = 'F'
        order.owner.save()
        order.save()
        return redirect('index')
    else:
        return HttpResponse('You must be a part of the order for making changes')

# REQUESTS
@login_required
def edit_request(request, requestid=None):
    if request.method == 'POST':
        # Form with filled data
        if requestid:
            currentRequest = Request.object.get(id=requestid)
            requestForm = NewRequestModelForm(request.POST, request.FILES, instance=currentRequest)
        else:
            requestForm = NewRequestModelForm(request.POST, request.FILES)

        newRequest = requestForm.save(commit=False)
        newRequest.community = Community.objects.get(id=request.session['currentCommunityId'])
        newRequest.owner = request.user
        newRequest.save()

        return redirect('index')
    elif requestid!=None:
        # Form for edition
        ap = Request.objects.get(id=requestid)
        requestForm = NewRequestModelForm(instance=ap)
    else:
        # Empty form
        requestForm = NewRequestModelForm()

    return render(request, 'auzonetweb/request.html', {'requestForm': requestForm})

# REST API
# Under construction...
