# coding=utf-8
import datetime

import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import BadHeaderError, EmailMessage
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext

from .forms import LoginForm, RegisterForm, NewRequestModelForm, JoinCommunityForm, \
    NewOfferModelForm, NewCommunityMsgModelForm, ProtectedCommunityForm, NewCommunityForm
from .models import Community, User, PublicUser, Request, Offer, CommunityMessage, Order

"""
Here is where the POST and GET request are processed
Auth API docs https://docs.djangoproject.com/en/1.9/topics/auth/default/
Customizing the authentication on Django https://docs.djangoproject.com/en/1.9/topics/auth/customizing/
"""
REQUEST_TYPE = 'R'
OFFER_TYPE = 'O'
KARMA_REWARD = 10
STATUS_ACTIVE = 'A'
STATUS_FINISHED = 'F'
STATUS_PENDING = 'P'
MESSAGE_TYPE_WARNING = 'W'
ORDER_TYPE_OFFER = 'O'
ORDER_TYPE_REQUEST = 'R'
ACCESS_TYPE_PRIVATE = 'PR'
PUBLIC_URL_BASE = 'http://apps.morelab.deusto.es/'


# INTERNATIONALIZATION: django-admin makemessages -l es AND django-admin makemessages -l en AND django-admin compilemessages

def access_control(comid, userid):
    accessing_community = get_object_or_404(Community, id=comid)
    logged_public_user = get_object_or_404(User, id=userid).publicuser

    if accessing_community.access_type == ACCESS_TYPE_PRIVATE:
        if accessing_community in logged_public_user.communities.all():
            return True
        else:
            return False
    else:
        return True


# COMMON PLACES
@login_required
def index(request, comid=None):
    # Check the community to load
    if comid is not None and access_control(comid, request.user.id):
        request.session['currentCommunityId'] = comid
        request.session['currentCommunityAddress'] = str(get_object_or_404(Community, id=comid))
    else:
        try:
            request.session['currentCommunityId'] = request.user.publicuser.communities.all()[0].id
            request.session['currentCommunityAddress'] = str(request.user.publicuser.communities.all()[0])
        except IndexError:
            # The user does not have community yet
            return redirect('wizard')

    # Load the community offers and requests
    community_offers = Offer.objects.filter(community=request.session['currentCommunityId']).exclude(
        status=STATUS_FINISHED).order_by('-date_published')
    community_requests = Request.objects.filter(community=request.session['currentCommunityId']).exclude(
        status=STATUS_FINISHED).order_by('-date_published')

    # Load the user related offerr, requests and active orders
    my_requests = Request.objects.filter(owner=request.user).exclude(status=STATUS_FINISHED).order_by('-date_published')
    my_offers = Offer.objects.filter(owner=request.user).exclude(status=STATUS_FINISHED).order_by('-date_published')
    my_orders = Order.objects.filter(Q(client=request.user) | Q(owner=request.user)).exclude(
        status=STATUS_FINISHED).exclude(status=STATUS_PENDING)

    # Load the public community messages
    community_messages = CommunityMessage.objects.filter(community=request.session['currentCommunityId']).order_by(
        '-date_published')
    paginator = Paginator(community_messages, 3)
    page = request.GET.get('page')

    try:
        paged_community_messages = paginator.page(page)
    except PageNotAnInteger:
        paged_community_messages = paginator.page(1)
    except EmptyPage:
        paged_community_messages = paginator.page(paginator.num_pages)

    # Community messages form
    if request.method == 'POST':
        # Form with filled data
        message_model_form = NewCommunityMsgModelForm(request.POST)
        if message_model_form.is_valid():
            new_message = message_model_form.save(commit=False)
            new_message.community = get_object_or_404(Community, id=request.session['currentCommunityId'])
            new_message.owner = request.user
            new_message.save()

            if new_message.message_type == MESSAGE_TYPE_WARNING:
                community_users = PublicUser.objects.filter(communities=request.session['currentCommunityId'])
                for up in community_users:
                    send_notification_email(None,
                                            up.user.email,
                                            ugettext(u"Nuevo aviso en ") + request.session['currentCommunityAddress'],
                                            ugettext(u"Nuevo aviso"),
                                            new_message.owner.first_name + ugettext(
                                                u" ha publicado el siguiente aviso en ") +
                                            request.session['currentCommunityAddress'] +
                                            u": " + new_message.message_text,
                                            ugettext(u"Ver el mensaje en la web"),
                                            PUBLIC_URL_BASE + 'auzonet/community/' + str(request.session[
                                                                                             'currentCommunityId']),
                                            PUBLIC_URL_BASE + request.user.publicuser.avatar.url
                                            )

            return redirect('indexcommunity', comid=request.session['currentCommunityId'])
        else:
            message_model_form = NewCommunityMsgModelForm(request.POST)
    else:
        message_model_form = NewCommunityMsgModelForm()

    return render(request, 'auzonetweb/index.html', {
        'offers': community_offers,
        'requests': community_requests,
        'myRequests': my_requests,
        'myOrders': my_orders,
        'myOffers': my_offers,
        'communityMessages': paged_community_messages,
        'messageModelForm': message_model_form
    })


@login_required
def user_profile(request):
    requests_published = Request.objects.all().filter(owner=request.user).order_by('-date_published')
    requests_attended = Order.objects.all().filter(order_type=ORDER_TYPE_REQUEST).filter(client=request.user)

    my_requests_active = Request.objects.all().filter(
        owner=request.user).exclude(status=STATUS_FINISHED)

    offers_published = Offer.objects.all().filter(owner=request.user).order_by('-date_published')
    offers_hired = Order.objects.all().filter(order_type=ORDER_TYPE_OFFER).filter(client=request.user)

    my_offers_active = Offer.objects.all().filter(owner=request.user).exclude(
        status=STATUS_FINISHED)

    my_finished_requests = Request.objects.filter(owner=request.user).filter(status=STATUS_FINISHED)
    my_finished_offers = Offer.objects.filter(owner=request.user).filter(status=STATUS_FINISHED)

    current_date = datetime.datetime.now()

    # Count requests for the chart
    requests_per_month = []
    for i in range(current_date.month):
        requests_per_month.append(0)

    for i in range(current_date.month):
        for r in requests_published:
            if (r.date_published.month == i + 1) and (r.date_published.year == current_date.year):
                requests_per_month[i] += 1

    # Count offers for the chart
    offers_per_month = []
    for i in range(current_date.month):
        offers_per_month.append(0)

    for i in range(current_date.month):
        for o in offers_published:
            if (o.date_published.month == i + 1) and (o.date_published.year == current_date.year):
                offers_per_month[i] += 1

    return render(request, 'auzonetweb/user-profile.html', {'currentUser': request.user,
                                                            'requests_attended': requests_attended,
                                                            'my_requests_active': my_requests_active,
                                                            'requests_published': requests_published,
                                                            'offers_published': offers_published,
                                                            'offers_hired': offers_hired,
                                                            'my_offers_active': my_offers_active,
                                                            'my_finished_offers': my_finished_offers,
                                                            'my_finished_requests': my_finished_requests,
                                                            'current_year': current_date.year,
                                                            'requests_per_month': requests_per_month,
                                                            'offers_per_month': offers_per_month})


@login_required
def delete_post(request, postid, posttype):
    p = ""
    if posttype == 'R':
        p = get_object_or_404(Request, id=postid)
        if p.owner.id == request.user.id:
            orders = Order.objects.filter(auzonetrequest=p)
            for o in orders:
                o.status = STATUS_FINISHED
                o.save()
        else:
            return HttpResponse(ugettext('Unauthorized'), status=401)
    elif posttype == 'O':
        p = get_object_or_404(Offer, id=postid)
        if p.owner.id == request.user.id:
            orders = Order.objects.filter(offer=p)
            for o in orders:
                o.status = STATUS_FINISHED
                o.save()
        else:
            return HttpResponse(ugettext('Unauthorized'), status=401)

    p.status = STATUS_FINISHED

    p.save()
    return redirect('indexcommunity', comid=request.session['currentCommunityId'])


@login_required
def recover_post(request, postid, posttype):
    p = ""
    if posttype == 'R':
        p = get_object_or_404(Request, id=postid)
    elif posttype == 'O':
        p = get_object_or_404(Offer, id=postid)

    if p.owner.id == request.user.id:
        p.status = STATUS_ACTIVE
        p.save()
    else:
        return HttpResponse(ugettext('Unauthorized'), status=401)

    return redirect('my-profile')


@login_required
def delete_message(request, messageid):
    message = get_object_or_404(CommunityMessage, id=messageid)
    if message.owner.id == request.user.id:
        message.delete()
    else:
        return HttpResponse(ugettext('Unauthorized'), status=401)

    return redirect('indexcommunity', comid=request.session['currentCommunityId'])


@login_required
def confirmation_success(request, orderid):
    order = get_object_or_404(Order, id=orderid)

    if request.user == order.owner:
        return render(request, 'auzonetweb/confirmation-success.html', {'order': order})
    else:
        return redirect('index')


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
            mailtext = order.client.first_name + ugettext(
                u" ha marcado como terminado el acuerdo sobre ") + order.offer.title + ugettext(
                u" y ha votado la experiencia como positiva, esto te añade 10 puntos de Karma que mejoran tu reputacion en la comunidad. ¡Felicidades!.")
        else:
            # Bad feedback
            order.owner.publicuser.karma -= KARMA_REWARD
            mailtext = order.client.first_name + ugettext(
                u" ha marcado como terminado el acuerdo sobre ") + order.offer.title + ugettext(
                u" y ha votado la experiencia como negativa, esto te resta 10 puntos de Karma que empeoran tu reputacion en la comunidad. ")

        # Mark that the client already has voted
        order.client_voted = True
        # Send notification
        order_link = None
        button_text = None
        if not order.owner_voted:
            button_text = ugettext(u"Terminar acuerdo")
            mailtext += ugettext(
                u"\n\n Ahora tienes que marcar como terminado tu tambien el acuerdo y valorar tu experiencia con ") + order.client.first_name + "."
            if order.order_type == ORDER_TYPE_OFFER:
                order_link = PUBLIC_URL_BASE + 'auzonet/detail-offer/' + str(order.offer.id) + '/'
            else:
                order_link = PUBLIC_URL_BASE + 'auzonet/detail-request/' + str(order.auzonetrequest.id) + '/'
        else:
            order.status = STATUS_FINISHED
        send_notification_email(None,
                                order.owner.email,
                                order.client.first_name + ugettext(u" ha marcado como finalizada la colaboracion"),
                                order.client.first_name + ugettext(u" ha marcado como finalizada la colaboracion"),
                                mailtext,
                                button_text,
                                order_link,
                                PUBLIC_URL_BASE + order.client.publicuser.avatar.url
                                )

        # Save the publicuser rating and the order new status
        order.owner.publicuser.save()
        order.save()
        return redirect('index')
    elif order.owner == request.user:
        # The owner is finalizing the order
        if feedback == '1':
            order.client.publicuser.karma += KARMA_REWARD
            mailtext = order.owner.first_name + ugettext(
                u" ha marcado como terminado el acuerdo sobre ") + order.offer.title + ugettext(
                u" y ha votado la experiencia como positiva, esto te añade 10 puntos de Karma que mejoran tu reputacion en la comunidad. ¡Felicidades!.")
        else:
            order.client.publicuser.karma -= KARMA_REWARD
            mailtext = order.owner.first_name + ugettext(
                u" ha marcado como terminado el acuerdo sobre ") + order.offer.title + ugettext(
                u" y ha votado la experiencia como negativa, esto te resta 10 puntos de Karma que empeoran tu reputacion en la comunidad.")
        # Mark that the owner already has voted
        order.owner_voted = True
        # Send notification
        order_link = None
        button_text = None
        if not order.client_voted:
            button_text = ugettext(u"Terminar acuerdo")
            mailtext += ugettext(
                "\n\n Ahora tienes que marcar como terminado tu tambien el acuerdo y valorar tu experiencia con ") + order.owner.first_name + "."
            if order.order_type == ORDER_TYPE_OFFER:
                order_link = PUBLIC_URL_BASE + 'auzonet/detail-offer/' + str(order.offer.id)
            else:
                order_link = PUBLIC_URL_BASE + 'auzonet/detail-request/' + str(order.auzonetrequest.id)
        else:
            order.status = STATUS_FINISHED
        send_notification_email(None,
                                order.client.email,
                                order.owner.first_name + ugettext(u" ha marcado como finalizada la colaboracion"),
                                order.owner.first_name + ugettext(u" ha marcado como finalizada la colaboracion"),
                                mailtext,
                                button_text,
                                order_link,
                                PUBLIC_URL_BASE + order.owner.publicuser.avatar.url
                                )
        # Save the publicuser rating and the order new status
        order.client.publicuser.save()
        order.save()
        return redirect('index')
    else:
        return HttpResponse(ugettext('Unauthorized'), status=401)


@login_required
def wizard(request):
    # Documentación http://apps.morelab.deusto.es/doc-welive/query-mapper/json-mapping.html
    # Dataset de portales https://dev.welive.eu/ods/dataset/portales-de-bilbao/resource/73b6103b-0c12-4b2c-98ae-71ed33e55e8c
    # Interfaz Swagger https://dev.welive.eu/dev/swagger/
    # DatasetID portales-de-bilbao
    # ResourceID 73b6103b-0c12-4b2c-98ae-71ed33e55e8c
    communities = Community.objects.all()

    # WELIVE API BOOTCAMP
    # Barrios de bilbao select distinct TBAR_DES_BARRIO_A, TTRE_COD_BARRIO from results;
    # Calles de cada barrio select distinct TPOR_COD_CALLE, TCAL_DES_CALLE_A from results where TTRE_COD_BARRIO = 701;
    # Portales con coordenadas select TPOR_DIR_PORTAL,TCOG_IDE_COORDX_UT,TCOG_IDE_COORDY_UT  from results where TBAR_DES_BARRIO_A = 'SAN IGNACIO' and TCAL_DES_CALLE_A='ZARANDOA'
    #
    url = 'https://dev.welive.eu/dev/api/ods/portales-de-bilbao/resource/73b6103b-0c12-4b2c-98ae-71ed33e55e8c/query'
    payload = 'select * from results limit 10;'

    # GET
    # r = requests.get(url)

    # GET with params in URL
    # r = requests.get(url, params=payload)

    # POST with form-encoded data
    # r = requests.post(url, data=payload)

    # POST with JSON
    # r = requests.post(url, data=payload)

    # Response, status etc
    # print r.text
    # print r.status_code

    # END WELIVE API

    if request.method == 'POST':
        if request.POST['formName'] == 'joinCommunity':
            select_community_form = JoinCommunityForm(request.POST)
            try:
                selected_community = get_object_or_404(Community, id=request.POST['community'])
            except ValueError:
                return render(request, 'auzonetweb/wizard.html',
                              {'newCommunityForm': NewCommunityForm(),
                               'selectCommunityForm': select_community_form,
                               'communities': communities,
                               'errorMessage': ugettext(u'Tienes que seleccionar una comunidad de la lista.'),
                               'modal': 'join'})
            if select_community_form.is_valid():
                # If the logged user is not already part of the joining community
                if selected_community not in request.user.publicuser.communities.all():
                    if selected_community.access_type == ACCESS_TYPE_PRIVATE:
                        return redirect('protectedcommunity', comid=selected_community.id)
                    else:
                        current_user = get_object_or_404(User, id=request.user.id)
                        current_user.publicuser.communities.add(selected_community)
                        current_user.save()
                        request.session['currentCommunityId'] = selected_community.id
                        request.session['currentCommunityAddress'] = str(selected_community)

                        send_notification_email(None,
                                                current_user.email,
                                                ugettext(u"Bienvenido a ") + str(selected_community),
                                                ugettext(u"Bienvenido a ") + str(selected_community),
                                                ugettext(
                                                    u"A partir de ahora, formas parte de tu comunidad de vecinos en Auzonet, ") +
                                                ugettext(u"estaras al dia de lo mas relevante que ocurra en ella. ") +
                                                ugettext(
                                                    u"Date una vuelta por la seccion de peticiones y ofertas por ") +
                                                ugettext(
                                                    u"si encuentras algo de tu interes. \n \n") + selected_community.welcome_message,
                                                ugettext(u"Ir a la web"),
                                                PUBLIC_URL_BASE + 'auzonet/community/' + str(selected_community.id),
                                                None
                                                )

                        return redirect('index')
                else:
                    # The user is already part of the community
                    return redirect('index')
            else:
                return render(request, 'auzonetweb/wizard.html',
                              {'newCommunityForm': NewCommunityForm(),
                               'selectCommunityForm': select_community_form,
                               'communities': communities,
                               'errorMessage': ugettext(u'Por favor, revisa los campos indicados'),
                               'modal': 'join'})
        elif request.POST['formName'] == 'newCommunity':
            new_community_form = NewCommunityForm(request.POST)
            if new_community_form.is_valid():

                # process the data in form.cleaned_data as required
                try:
                    new_neighborhood = Community(
                        access_type=new_community_form.cleaned_data['access_type'],
                        neighborhood_code=new_community_form.cleaned_data['neighborhood_code'],
                        neighborhood_name=new_community_form.cleaned_data['neighborhood_name'],
                        street_code=new_community_form.cleaned_data['street_code'],
                        street_name=new_community_form.cleaned_data['street_name'],
                        door_code=new_community_form.cleaned_data['door_code'],
                        coordinatesX=new_community_form.cleaned_data['coordinatesX'],
                        coordinatesY=new_community_form.cleaned_data['coordinatesY'],
                        password=new_community_form.cleaned_data['password'],
                        welcome_message=new_community_form.cleaned_data['welcome_message']
                    )
                    # Check if the community already exists
                    try:
                        Community.objects.get(neighborhood_code=new_neighborhood.neighborhood_code, street_code=new_neighborhood.street_code, door_code=new_neighborhood.door_code)
                        return render(request, 'auzonetweb/wizard.html',
                                      {'newCommunityForm': new_community_form, 'selectCommunityForm': JoinCommunityForm(),
                                       'communities': communities,
                                       'errorMessage': ugettext(
                                           u'La comunidad que intentas crear ya existe, búscala en la opción unirme a comunidad existente.'),
                                       'modal': 'new'})
                    except ObjectDoesNotExist:
                        new_neighborhood.save()

                        current_user = get_object_or_404(User, id=request.user.id)
                        current_user.publicuser.communities.add(new_neighborhood)
                        current_user.save()
                        request.session['currentCommunityId'] = new_neighborhood.id
                        request.session['currentCommunityAddress'] = str(new_neighborhood)

                        return redirect('indexcommunity', comid=new_neighborhood.id)
                except IntegrityError:
                    return render(request, 'auzonetweb/wizard.html',
                                  {'newCommunityForm': new_community_form, 'selectCommunityForm': JoinCommunityForm(),
                                   'communities': communities,
                                   'errorMessage': ugettext(u'Por favor, revisa los campos indicados'),
                                   'modal': 'new'})
            else:
                return render(request, 'auzonetweb/wizard.html',
                              {'newCommunityForm': new_community_form, 'selectCommunityForm': JoinCommunityForm(),
                               'communities': communities,
                               'errorMessage': ugettext(u'Por favor, revisa los campos indicados'),
                               'modal': 'new'})
    else:
        new_community_form = NewCommunityForm()
        select_community_form = JoinCommunityForm()

    return render(request, 'auzonetweb/wizard.html',
                  {'newCommunityForm': new_community_form, 'selectCommunityForm': select_community_form,
                   'communities': communities})


@login_required
def protected_community(request, comid):
    community = get_object_or_404(Community, id=comid)

    if request.method == 'POST':
        protected_community_form = ProtectedCommunityForm(request.POST)
        if protected_community_form.is_valid():
            # Do things
            if community.password == protected_community_form.cleaned_data['password']:
                # Unirse
                current_user = get_object_or_404(User, id=request.user.id)
                current_user.publicuser.communities.add(community)
                current_user.save()
                request.session['currentCommunityId'] = community.id
                request.session['currentCommunityAddress'] = str(community)

                send_notification_email(None,
                                        current_user.email,
                                        ugettext(u"Bienvenido a ") + str(community),
                                        ugettext(u"Bienvenido a ") + str(community),
                                        ugettext(
                                            u"A partir de ahora, formas parte de tu comunidad de vecinos en Auzonet, ") +
                                        ugettext(u"estaras al dia de lo mas relevante que ocurra en ella. ") +
                                        ugettext(u"Date una vuelta por la seccion de peticiones y ofertas por ") +
                                        ugettext(
                                            u"si encuentras algo de tu interes. \n \n") + community.welcome_message,
                                        ugettext(u"Ir a la web"),
                                        PUBLIC_URL_BASE + 'auzonet/community/' + str(community.id),
                                        None
                                        )

                return redirect('indexcommunity', comid=community.id)
            else:
                # Contraseña incorrecta
                error_message = u"Contraseña incorrecta"
                protected_community_form = ProtectedCommunityForm()

                return render(request, 'auzonetweb/protected-community.html', {"errorMessage": error_message,
                                                                               "address": str(community),
                                                                               "protectedCommunityForm": protected_community_form
                                                                               })
        else:
            # A tu casa no me times
            return redirect('protectedcommunity', comid=comid)
    else:
        protected_community_form = ProtectedCommunityForm()

    return render(request, 'auzonetweb/protected-community.html', {"address": str(community),
                                                                   "protectedCommunityForm": protected_community_form
                                                                   })


def welcome(request):
    if request.user.is_authenticated():
        return redirect('index')
    else:
        # if this is a POST request we need to process the form data
        next = ""
        if request.GET:
            next = request.GET['next']
        if request.method == 'POST':
            login_form = LoginForm(request.POST)
            register_form = RegisterForm(request.POST, request.FILES)
            if request.POST['formtype'] == 'login':
                # check whether it's valid:
                if login_form.is_valid():
                    # process the data in form.cleaned_data as required
                    username = request.POST['username']
                    password = request.POST['password']
                    user = authenticate(username=username, password=password)
                    if user is not None:
                        if user.is_active:
                            login(request, user)
                            try:
                                request.session['currentCommunityId'] = request.user.publicuser.communities.all()[0].id
                                request.session['currentCommunityAddress'] = str(request.user.publicuser.communities.all()[
                                    0])
                                # Redirect to a success page.
                                if next:
                                    return redirect(next)
                                else:
                                    return redirect('indexcommunity',
                                                    comid=request.user.publicuser.communities.all()[0].id)
                            except IndexError:
                                # The user does not have community yet
                                return redirect('wizard')
                        else:
                            # Return a 'disabled account' error message
                            return redirect('welcome')
                    else:
                        # Return an 'invalid login' error message.
                        return render(request, 'auzonetweb/welcome.html',
                                      {'loginForm': login_form, 'registerForm': RegisterForm(),
                                       'errorMessage': ugettext(u'Usuario o contraseña incorrectos'), 'modal': 'login'})
                else:
                    return render(request, 'auzonetweb/welcome.html',
                                  {'loginForm': login_form, 'registerForm': RegisterForm(),
                                   'errorMessage': ugettext(u'Por favor, revise los campos indicados'),
                                   'modal': 'login'})
            elif request.POST['formtype'] == 'register':
                # check whether it's valid:
                if register_form.is_valid():
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
                                                ugettext(u"Bienvenido a Auzonet"),
                                                ugettext(u"Bienvenido a Auzonet"),
                                                ugettext(u"Gracias por registrarte") + u" " + first_name + ugettext(
                                                    u", busca tu comunidad entre las que ya estan ") +
                                                ugettext(
                                                    u"registradas o crea la tuya para empezar a disfrutar de todo lo que ") +
                                                ugettext(u"ofrece el servicio"),
                                                None,
                                                None,
                                                None
                                                )
                    except IntegrityError:
                        return render(request, 'auzonetweb/welcome.html',
                                      {'loginForm': LoginForm(), 'registerForm': register_form,
                                       'errorMessage': ugettext(u'El nombre de usuario ya existe.'),
                                       'modal': 'register'})

                    user = authenticate(username=username, password=password)
                    login(request, user)

                    # Send a confirmation email
                    return redirect('wizard')
                else:
                    return render(request, 'auzonetweb/welcome.html',
                                  {'loginForm': LoginForm(), 'registerForm': register_form,
                                   'errorMessage': ugettext(u'Por favor, revise los campos indicados'),
                                   'modal': 'register'})
        else:
            login_form = LoginForm()
            register_form = RegisterForm()

        return render(request, 'auzonetweb/welcome.html', {'loginForm': login_form, 'registerForm': register_form})


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
            return render(request, 'auzonetweb/Offer/edit-offer.html',
                          {'offerForm': offerForm,
                           'errorMessage': ugettext(u'Por favor, revisa los campos indicados.')})

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

    return render(request, 'auzonetweb/Offer/edit-offer.html', {'offerForm': offerForm})


@login_required
def detail_offer(request, offerid):
    # Obtain the offer shown
    offer = get_object_or_404(Offer, id=offerid)
    if access_control(offer.community_id, request.user.id):
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

        return render(request, 'auzonetweb/Offer/show-offer.html',
                      {'offer': offer, 'orders': orders, 'is_client': is_client, 'client_order': client_order})
    else:
        return redirect('index')


@login_required
def accept_offer(request, orderid):
    order = get_object_or_404(Order, id=orderid)

    if request.user == order.offer.owner:
        if order.status != STATUS_ACTIVE:

            # The logged user is the owner
            order.status = STATUS_ACTIVE
            order.save()

            send_notification_email(None,
                                    order.client.email,
                                    order.offer.owner.first_name + ugettext(u" ha aceptado trabajar contigo"),
                                    ugettext(u"Acuerdo aceptado"),
                                    order.offer.owner.first_name + ugettext(
                                        u" ha aceptado el acuerdo sobre ") +
                                    order.offer.title +
                                    ugettext(
                                        u" recuerda marcar como finalizado el acuerdo cuando lo consideres terminado.") +
                                    ugettext(u" Puedes ponerte en contacto con ") +
                                    order.offer.owner.first_name +
                                    ugettext(u" a traves de su email ") +
                                    order.offer.owner.email,
                                    ugettext(u"Ver la oferta"),
                                    PUBLIC_URL_BASE + "auzonet/detail-offer/" + str(order.offer.id) + "/",
                                    PUBLIC_URL_BASE + order.offer.owner.publicuser.avatar.url
                                    )

            return redirect('confirmation-success', orderid=orderid)
        else:
            return HttpResponse('You already have accepted this offer.')
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
    subject = ugettext(u"Auzonet: ") + userInterested.username + ugettext(u" esta interesado en tu oferta.")
    subtitle = ugettext(u'Me interesa')
    content = ugettext(u'El usuario ') + userInterested.username + ugettext(
        u' esta interesado en tu oferta ') + offer.title
    buttonText = ugettext('Aceptar solicitud')
    buttonLink = PUBLIC_URL_BASE + 'auzonet/accept-offer/' + str(order.id)
    avatarLink = PUBLIC_URL_BASE + userInterested.publicuser.avatar.url

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
            return render(request, 'auzonetweb/Request/edit-request.html',
                          {'requestForm': requestForm,
                           'errorMessage': ugettext(u'Por favor, revisa los campos indicados.')})

        return redirect('detail-request', requestid=newRequest.id)
    elif requestid is not None:
        # Form for edition
        ap = get_object_or_404(Request, id=requestid)
        if ap.owner.id == request.user.id:
            requestForm = NewRequestModelForm(instance=ap)
        else:
            return HttpResponse(ugettext('Unauthorized'), status=401)
    else:
        # Empty form
        requestForm = NewRequestModelForm()

    return render(request, 'auzonetweb/Request/edit-request.html', {'requestForm': requestForm})


@login_required
def detail_request(request, requestid):
    # Obtain the request shown
    auzonetrequest = get_object_or_404(Request, id=requestid)
    if access_control(auzonetrequest.community_id, request.user.id):
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

        return render(request, 'auzonetweb/Request/show-request.html',
                      {'auzonetrequest': auzonetrequest, 'requests': requests, 'is_client': is_client,
                       'client_order': client_order})
    else:
        return redirect('index')


@login_required
def accept_request(request, orderid):
    order = get_object_or_404(Order, id=orderid)

    if request.user == order.auzonetrequest.owner:
        # The logged user is the owner
        if order.status != STATUS_ACTIVE:
            order.status = STATUS_ACTIVE
            order.save()

            send_notification_email(None,
                                    order.client.email,
                                    order.auzonetrequest.owner.first_name + ugettext(u" ha aceptado tu ayuda"),
                                    ugettext(u"Acuerdo aceptado"),
                                    order.auzonetrequest.owner.first_name +
                                    ugettext(
                                        u" ha aceptado el acuerdo sobre ") +
                                    order.auzonetrequest.title +
                                    ugettext(
                                        u" recuerda marcar como finalizado el acuerdo cuando lo consideres terminado.") +
                                    ugettext(u" Puedes ponerte en contacto con ") +
                                    order.auzonetrequest.owner.first_name +
                                    ugettext(u" a traves de su email ") +
                                    order.auzonetrequest.owner.email,
                                    ugettext(u"Ver la peticion"),
                                    PUBLIC_URL_BASE + "auzonet/detail-request/" + str(order.auzonetrequest.id) + "/",
                                    PUBLIC_URL_BASE + order.auzonetrequest.owner.publicuser.avatar.url
                                    )

            return redirect('confirmation-success', orderid=orderid)
        else:
            return HttpResponse('You already have accepted this request')
    else:
        # The logged user is not the owner
        return HttpResponse(ugettext('Unauthorized'), status=401)


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
    subject = ugettext(u"Auzonet: ") + userInterested.username + ugettext(u" quiere atender tu peticion")
    subtitle = ugettext(u'¿Te echo una mano?')
    content = ugettext(u'El usuario ') + userInterested.username + ugettext(
        u' quiere atender tu peticion ') + auzonetrequest.title
    buttonText = ugettext(u'Aceptar colaboración')
    buttonLink = PUBLIC_URL_BASE + 'auzonet/accept-request/' + str(order.id)
    avatarLink = PUBLIC_URL_BASE + userInterested.publicuser.avatar.url

    send_notification_email(fromEmail, toEmail, subject, subtitle, content, buttonText, buttonLink, avatarLink)

    return redirect('index')


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
