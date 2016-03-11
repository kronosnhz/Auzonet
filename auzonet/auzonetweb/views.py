# coding=utf-8
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect, render_to_response, get_object_or_404
from django.template import RequestContext, Context
from django.template.loader import get_template

from .forms import LoginForm, RegisterForm, NewCommunityModelForm, NewRequestModelForm, JoinCommunityForm, \
    NewOfferModelForm, NewCommunityMsgModelForm
from .models import Community, User, PublicUser, Request, Offer, CommunityMessage, Order

"""
Here is where the POST and GET request are processed
Auth API docs https://docs.djangoproject.com/en/1.9/topics/auth/default/
Customizing the authentication on Django https://docs.djangoproject.com/en/1.9/topics/auth/customizing/
"""
OFFER_TYPE = 'O'
REQUEST_TYPE = 'R'
KARMA_REWARD = 10
STATUS_ACTIVE = 'A'
STATUS_FINISHED = 'F'
STATUS_PENDING = 'P'


# COMMON PLACES
@login_required
def index(request, comid=None):
    if comid is not None:
        request.session['currentCommunityId'] = comid
        request.session['currentCommunityAddress'] = get_object_or_404(Community, id=comid).address
    else:
        request.session['currentCommunityId'] = request.user.publicuser.communities.all()[0].id
        request.session['currentCommunityAddress'] = request.user.publicuser.communities.all()[0].address

    offers = Offer.objects.filter(community=request.session['currentCommunityId']).exclude(
        status=STATUS_FINISHED).order_by('-date_published')
    requests = Request.objects.filter(community=request.session['currentCommunityId']).exclude(
        status=STATUS_FINISHED).order_by('-date_published')

    myRequests = Request.objects.filter(owner=request.user).exclude(status=STATUS_FINISHED).order_by('-date_published')
    myOffers = Offer.objects.filter(owner=request.user).exclude(status=STATUS_FINISHED).order_by('-date_published')
    communityMessages = CommunityMessage.objects.filter(community=request.session['currentCommunityId']).order_by(
        '-date_published')

    myOrders = Order.objects.filter(client=request.user).exclude(status=STATUS_FINISHED).exclude(status=STATUS_PENDING)

    if request.method == 'POST':
        # Form with filled data
        messageModelForm = NewCommunityMsgModelForm(request.POST)
        newMessage = messageModelForm.save(commit=False)
        newMessage.community = get_object_or_404(Community, id=request.session['currentCommunityId'])
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
        'myOffers': myOffers,
        'communityMessages': communityMessages,
        'messageModelForm': messageModelForm
    })


@login_required
def user_profile(request):
    return render(request, 'auzonetweb/user-profile.html', {'currentUser': request.user})


@login_required
def delete_post(request, postid, posttype):
    if posttype == 'R':
        p = get_object_or_404(Request, id=postid)
        if p.owner.id == request.user.id:
            orders = Order.objects.filter(auzonetrequest=p)
            for o in orders:
                o.status = STATUS_FINISHED
                o.save()
        else:
            return HttpResponse('Unauthorized', status=401)
    elif posttype == 'O':
        p = get_object_or_404(Offer, id=postid)
        if p.owner.id == request.user.id:
            orders = Order.objects.filter(offer=p)
            for o in orders:
                o.status = STATUS_FINISHED
                o.save()
        else:
            return HttpResponse('Unauthorized', status=401)

    p.status = STATUS_FINISHED

    p.save()
    return redirect('index')


@login_required
def delete_message(request, messageid):
    message = get_object_or_404(CommunityMessage, id=messageid)
    if message.owner.id == request.user.id:
        message.delete()
    else:
        return HttpResponse('Unauthorized', status=401)

    return redirect('index')


@login_required
def confirmation_success(request):
    return render(request, 'auzonetweb/confirmation-success.html')


@login_required
def finalize_order(request, orderid, feedback):
    # Get the order
    order = get_object_or_404(Order, id=orderid)
    # Check wether is the owner or the client
    if order.client == request.user:
        # The client is finalizing the order
        if feedback == '1':
            # Good feedback
            order.owner.publicuser.karma += KARMA_REWARD
        else:
            # Bad feedback
            order.owner.publicuser.karma -= KARMA_REWARD
        # Mark that the client already has voted
        order.client_voted = True
        # Check if the owner has voted also for finishing the order
        if order.owner_voted:
            order.status = STATUS_FINISHED
        # Save the publicuser rating and the order new status
        order.owner.publicuser.save()
        order.save()
        return redirect('index')
    elif order.owner == request.user:
        # The owner is finalizing the order
        if feedback == '1':
            order.client.publicuser.karma += KARMA_REWARD
        else:
            order.client.publicuser.karma -= KARMA_REWARD
        # Mark that the owner already has voted
        order.owner_voted = True
        # Check if the client has voted also for finishing the order
        if order.client_voted:
            order.status = STATUS_FINISHED
        # Save the publicuser rating and the order new status
        order.client.publicuser.save()
        order.save()
        return redirect('index')
    else:
        return HttpResponse('Unauthorized', status=401)


@login_required
def wizard(request):
    # Documentación http://apps.morelab.deusto.es/doc-welive/query-mapper/json-mapping.html
    # Dataset de portales https://dev.welive.eu/ods/dataset/portales-de-bilbao/resource/73b6103b-0c12-4b2c-98ae-71ed33e55e8c
    # Interfaz Swagger https://dev.welive.eu/dev/swagger/
    communities = Community.objects.all()

    if request.method == 'POST':
        if request.POST['formName'] == 'joinCommunity':
            selectCommunityForm = JoinCommunityForm(request.POST)
            selectedCommunity = get_object_or_404(Community, id=request.POST['community'])
            if selectCommunityForm.is_valid():
                currentUser = get_object_or_404(User, id=request.user.id)
                currentUser.publicuser.communities.add(selectedCommunity)
                currentUser.save()
                request.session['currentCommunityId'] = selectedCommunity.id
                request.session['currentCommunityAddress'] = selectedCommunity.address
                return redirect('index')
        elif request.POST['formName'] == 'newCommunity':
            newCommunityModelForm = NewCommunityModelForm(request.POST)
            if newCommunityModelForm.is_valid():
                newCommunity = newCommunityModelForm.save()

                currentUser = get_object_or_404(User, id=request.user.id)
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

    return render(request, 'auzonetweb/wizard.html',
                  {'newCommunityForm': newCommunityModelForm, 'selectCommunityForm': selectCommunityForm,
                   'communities': communities})


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
                            request.session['currentCommunityAddress'] = request.user.publicuser.communities.all()[
                                0].address
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

        return render(request, 'auzonetweb/welcome.html', {'loginForm': loginForm, 'registerForm': registerForm})


def bootcamp(request):
    datasetsjson = requests.get('https://dev.welive.eu/dev/api/ods/dataset/all').json()
    portalesjson = requests.get(
        'https://dev.welive.eu/dev/api/ods/dataset/portales-de-bilbao/resource/73b6103b-0c12-4b2c-98ae-71ed33e55e8c').json()

    return render(request, 'auzonetweb/bootcamp.html', {'datasetsjson': datasetsjson, 'portalesjson': portalesjson})


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
            currentOffer = get_object_or_404(Offer, id=offerid)
            offerForm = NewOfferModelForm(request.POST, request.FILES, instance=currentOffer)
        else:
            offerForm = NewOfferModelForm(request.POST, request.FILES)

        newOffer = offerForm.save(commit=False)
        newOffer.community = get_object_or_404(Community, id=request.session['currentCommunityId'])
        newOffer.owner = request.user
        newOffer.save()
        return redirect('indexcommunity', comid=request.session['currentCommunityId'])

    elif offerid is not None:
        # Form for edition
        ap = get_object_or_404(Offer, id=offerid)
        if ap.owner.id == request.user.id:
            offerForm = NewOfferModelForm(instance=ap)
        else:
            return HttpResponse('Unauthorized', status=401)
    else:
        # Empty form
        offerForm = NewOfferModelForm()

    return render(request, 'auzonetweb/Offer/offer.html', {'offerForm': offerForm})


@login_required
def detail_offer(request, offerid):
    # Obtain the offer shown
    offer = get_object_or_404(Offer, id=offerid)
    # Get the non-finished orders related to this offer
    orders = Order.objects.filter(offer=offer).exclude(status=STATUS_FINISHED).exclude(status=STATUS_PENDING)
    # Check if the logged user is client of this offer and the corresponding order
    is_client = 0
    client_order = None
    for o in orders:
        # Is the current user client of this order?
        if o.client == request.user:
            is_client = 1
            client_order = o

    return render(request, 'auzonetweb/Offer/detail-offer.html',
                  {'offer': offer, 'orders': orders, 'is_client': is_client, 'client_order': client_order})


@login_required
def accept_offer(request, orderid):
    order = get_object_or_404(Order, id=orderid)

    if request.user == order.offer.owner:
        # The logged user is the owner
        order.status = STATUS_ACTIVE
        order.save()

        return redirect('confirmation-success')
    else:
        # The logged user is not the owner
        return HttpResponse('Unauthorized', status=401)


@login_required
def hire_offer(request, offerid):
    offer = get_object_or_404(Offer, id=offerid)
    userOwner = offer.owner
    userInterested = request.user
    # The logged user is the owner
    order = Order()
    order.order_type = OFFER_TYPE
    order.owner = userOwner
    order.client = userInterested
    order.offer = offer
    order.status = STATUS_PENDING
    order.save()

    # Email notification
    subject = "Auzonet: " + userInterested.username + " esta interesado en tu oferta."

    ctx = {
        'subtitle':'Me interesa',
        'content':'El usuario ' + userInterested.username + ' esta interesado en tu oferta ' + offer.title,
        'buttontext':'Aceptar solicitud',
        'buttonlink':reverse('accept-offer', kwargs={'orderid': order.id}),
        'userInterested': userInterested,
        'offer': offer.title,
        'acceptlink': reverse('accept-offer', kwargs={'orderid': order.id})
    }

    message = get_template('auzonetweb/Mail/hire.html').render(Context(ctx))

    from_email = userInterested.email
    if subject and message and from_email:
        try:
            msg = EmailMessage(subject, message, from_email, [offer.owner.email])
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send()
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return redirect('index')
    else:
        # In reality we'd use a form class
        # to get proper validation errors.
        return HttpResponse('Make sure all fields are entered and valid.')


# REQUESTS
@login_required
def edit_request(request, requestid=None):
    if request.method == 'POST':
        # Form with filled data
        if requestid:
            currentRequest = get_object_or_404(Request, id=requestid)
            requestForm = NewRequestModelForm(request.POST, request.FILES, instance=currentRequest)
        else:
            requestForm = NewRequestModelForm(request.POST, request.FILES)

        newRequest = requestForm.save(commit=False)
        newRequest.community = get_object_or_404(Community, id=request.session['currentCommunityId'])
        newRequest.owner = request.user
        newRequest.save()

        return redirect('indexcommunity', comid=request.session['currentCommunityId'])
    elif requestid is not None:
        # Form for edition
        ap = get_object_or_404(Request, id=requestid)
        if ap.owner.id == request.user.id:
            requestForm = NewRequestModelForm(instance=ap)
        else:
            return HttpResponse('Unauthorized', status=401)
    else:
        # Empty form
        requestForm = NewRequestModelForm()

    return render(request, 'auzonetweb/Request/request.html', {'requestForm': requestForm})


@login_required
def detail_request(request, requestid):
    # Obtain the request shown
    auzonetrequest = get_object_or_404(Request, id=requestid)
    # Get the non-finished orders related to this request
    orders = Order.objects.filter(auzonetrequest=auzonetrequest).exclude(status=STATUS_FINISHED).exclude(
        status=STATUS_PENDING)
    # Check if the logged user is client of this offer and the corresponding order
    is_client = 0
    client_order = None
    for o in orders:
        # Is the current user client of this order?
        if o.client == request.user:
            is_client = 1
            client_order = o

    return render(request, 'auzonetweb/Request/detail-request.html',
                  {'auzonetrequest': auzonetrequest, 'requests': requests, 'is_client': is_client,
                   'client_order': client_order})


@login_required
def accept_request(request, orderid):
    order = Order.objects.get_object_or_404(id=orderid)

    if request.user == order.auzonetrequest.owner:
        # The logged user is the owner
        order.status = STATUS_ACTIVE
        order.save()

        return redirect('confirmation-success')
    else:
        # The logged user is not the owner
        return HttpResponse('Unauthorized', status=401)


@login_required
def hire_request(request, requestid):
    auzonetrequest = get_object_or_404(Request, id=requestid)
    userOwner = auzonetrequest.owner
    userInterested = request.user
    # The logged user is the owner
    order = Order()
    order.order_type = REQUEST_TYPE
    order.owner = userOwner
    order.client = userInterested
    order.auzonetrequest = auzonetrequest
    order.status = STATUS_PENDING
    order.save()

    # Email notification
    subject = userInterested.username + " quiere atender tu peticion"
    html_message = userInterested.username + " esta interesado en atender tu peticion " + auzonetrequest.title + ". Pulsa <a href=" + reverse(
        'accept-request', kwargs={'orderid': order.id}) + ">aqui</a> para aceptar su ofrecimiento."
    from_email = userInterested.email
    if subject and html_message and from_email:
        try:
            send_mail(subject, html_message, from_email, [auzonetrequest.owner.email])
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return redirect('index')
    else:
        # In reality we'd use a form class
        # to get proper validation errors.
        return HttpResponse('Make sure all fields are entered and valid.')


# SUPPORTING VIEWS
def handler404(request):
    response = render_to_response('auzonetweb/Support/404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('auzonetweb/500.html', {}, context_instance=RequestContext(request))
    response.status_code = 500
    return response

# EMAIL TEMPLATES
def email_hire(request):
    subject = "I am an HTML email"
    to = ['buddy@buddylindsey.com']
    from_email = 'test@example.com'

    ctx = {
        'user': 'buddy',
        'purchase': 'Books'
    }

    message = get_template('main/email/email.html').render(Context(ctx))
    msg = EmailMessage(subject, message, to=to, from_email=from_email)
    msg.content_subtype = 'html'
    msg.send()

    return HttpResponse('email_two')
# REST API
# Under construction...
