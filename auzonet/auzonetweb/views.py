# coding=utf-8
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render, redirect, render_to_response, get_object_or_404
from django.template import RequestContext, Context
from django.template.loader import get_template
from django.db.models import Q

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
MESSAGE_TYPE_WARNING = 'W'

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

    myOrders = Order.objects.filter(Q(client=request.user) | Q(owner=request.user)).exclude(status=STATUS_FINISHED).exclude(status=STATUS_PENDING)

    if request.method == 'POST':
        # Form with filled data
        messageModelForm = NewCommunityMsgModelForm(request.POST)
        newMessage = messageModelForm.save(commit=False)
        newMessage.community = get_object_or_404(Community, id=request.session['currentCommunityId'])
        newMessage.owner = request.user
        newMessage.save()

        if newMessage.message_type == MESSAGE_TYPE_WARNING:
            communityUsers = PublicUser.objects.filter(communities=request.session['currentCommunityId'])
            for up in communityUsers:
                send_notification_email(None,
                                        up.user.email,
                                        "Nuevo aviso en " + request.session['currentCommunityAddress'],
                                        "Nuevo aviso",
                                        newMessage.owner.first_name + " ha publicado un aviso importante en " + request.session['currentCommunityAddress'],
                                        "Ver aviso",
                                        reverse('indexcommunity', kwargs={'comid': request.session['currentCommunityId']}),
                                        request.user.publicuser.avatar.url
                                        )

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
            try:
                selectedCommunity = get_object_or_404(Community, id=request.POST['community'])
            except ValueError:
                return render(request, 'auzonetweb/wizard.html',
                              {'newCommunityForm': NewCommunityModelForm(), 'selectCommunityForm': selectCommunityForm,
                               'communities': communities,
                               'errorMessage': 'Tienes que seleccionar una comunidad de la lista.', 'modal': 'join'})
            if selectCommunityForm.is_valid():
                currentUser = get_object_or_404(User, id=request.user.id)
                currentUser.publicuser.communities.add(selectedCommunity)
                currentUser.save()
                request.session['currentCommunityId'] = selectedCommunity.id
                request.session['currentCommunityAddress'] = selectedCommunity.address
                return redirect('index')
            else:
                return render(request, 'auzonetweb/wizard.html',
                              {'newCommunityForm': NewCommunityModelForm(), 'selectCommunityForm': selectCommunityForm,
                               'communities': communities, 'errorMessage': 'Por favor, revisa los campos indicados',
                               'modal': 'join'})
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
                return render(request, 'auzonetweb/wizard.html',
                              {'newCommunityForm': newCommunityModelForm, 'selectCommunityForm': JoinCommunityForm(),
                               'communities': communities, 'errorMessage': 'Por favor, revisa los campos indicados',
                               'modal': 'new'})
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
                        return render(request, 'auzonetweb/welcome.html',
                                      {'loginForm': loginForm, 'registerForm': RegisterForm(),
                                       'errorMessage': 'Usuario o contraseña incorrectos', 'modal': 'login'})
                else:
                    return render(request, 'auzonetweb/welcome.html',
                                  {'loginForm': loginForm, 'registerForm': RegisterForm(),
                                   'errorMessage': 'Por favor, revise los campos indicados', 'modal': 'login'})
            elif request.POST['formtype'] == 'register':
                # check whether it's valid:
                if registerForm.is_valid():
                    # process the data in form.cleaned_data as required
                    username = request.POST['username']
                    email = request.POST['email']
                    first_name = request.POST['first_name']
                    last_name = request.POST['last_name']
                    password = request.POST['password']
                    birthdate = request.POST['birthdate']
                    avatar = request.FILES['avatar']

                    try:
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
                        send_notification_email(None,
                                                email,
                                                "Bienvenido a Auzonet",
                                                "Bienvenido a Auzonet",
                                                "Gracias por registrarte" + first_name + ", busca tu comunidad entre las que ya están " +
                                                "registradas o crea la tuya para empezar a disfrutar de todo lo que " +
                                                "ofrece el servicio",
                                                None,
                                                None,
                                                None
                                                )
                    except IntegrityError:
                        return render(request, 'auzonetweb/welcome.html',
                                      {'loginForm': LoginForm(), 'registerForm': registerForm,
                                       'errorMessage': 'El nombre de usuario ya existe.', 'modal': 'register'})

                    user = authenticate(username=username, password=password)
                    login(request, user)

                    # Send a confirmation email


                    return redirect('wizard')
                else:
                    return render(request, 'auzonetweb/welcome.html',
                                  {'loginForm': LoginForm(), 'registerForm': registerForm,
                                   'errorMessage': 'Por favor, revise los campos indicados', 'modal': 'register'})
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

        if offerForm.is_valid():
            newOffer = offerForm.save(commit=False)
            newOffer.community = get_object_or_404(Community, id=request.session['currentCommunityId'])
            newOffer.owner = request.user
            newOffer.save()
            return redirect('detail-offer', offerid=newOffer.id)
        else:
            return render(request, 'auzonetweb/Offer/offer.html',
                          {'offerForm': offerForm, 'errorMessage': 'Por favor, revisa los campos indicados.'})

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

    fromEmail = userInterested.email
    toEmail = offer.owner.email
    subject = "Auzonet: " + userInterested.username + " esta interesado en tu oferta."
    subtitle = 'Me interesa'
    content = 'El usuario ' + userInterested.username + ' esta interesado en tu oferta ' + offer.title
    buttonText = 'Aceptar solicitud'
    buttonLink = reverse('accept-offer', kwargs={'orderid': order.id})
    avatarLink = userInterested.publicuser.avatar.url

    send_notification_email(fromEmail, toEmail, subject, subtitle, content, buttonText, buttonLink, avatarLink)

    return redirect('index')


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

        if requestForm.is_valid():
            newRequest = requestForm.save(commit=False)
            newRequest.community = get_object_or_404(Community, id=request.session['currentCommunityId'])
            newRequest.owner = request.user
            newRequest.save()
        else:
            return render(request, 'auzonetweb/Request/request.html',
                          {'requestForm': requestForm, 'errorMessage': 'Por favor, revisa los campos indicados.'})

        return redirect('detail-request', requestid=newRequest.id)
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

    fromEmail = userInterested.email
    toEmail = userOwner.email
    subject = "Auzonet: " + userInterested.username + " quiere atender tu peticion"
    subtitle = '¿Te echo una mano?'
    content = 'El usuario ' + userInterested.username + ' quiere atender tu peticion ' + auzonetrequest.title
    buttonText = 'Aceptar colaboración'
    buttonLink = reverse('accept-request', kwargs={'requestid': auzonetrequest.id})
    avatarLink = userInterested.publicuser.avatar.url

    send_notification_email(fromEmail, toEmail, subject, subtitle, content, buttonText, buttonLink, avatarLink)

    return redirect('index')


# SUPPORTING VIEWS
def handler404(request):
    response = render_to_response('auzonetweb/Support/404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('auzonetweb/500.html', {}, context_instance=RequestContext(request))
    response.status_code = 500
    return response


# REST API
# Under construction...

# EMAIL
def send_notification_email(fromEmail, toEmail, subject, subtitle, content, buttonText, buttonLink, avatarLink):
    # Email notification
    ctx = {
        'subtitle': subtitle,
        'content': content,
        'buttontext': buttonText,
        'buttonlink': buttonLink,
        'avatarlink': avatarLink,
    }

    message = get_template('auzonetweb/Mail/notification.html').render(Context(ctx))

    try:
        msg = EmailMessage(subject, message, fromEmail, [toEmail])
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send()
    except BadHeaderError:
        return HttpResponse('Invalid header found.')
