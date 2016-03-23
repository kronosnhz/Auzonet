from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^my-profile/$', views.user_profile, name='my-profile'),
    url(r'^delete-post/(?P<postid>\d+)/(?P<posttype>["R","O"]+)/$', views.delete_post, name='delete-post'),
    url(r'^delete-message/(?P<messageid>\d+)/$', views.delete_message, name='delete-message'),
    url(r'^confirmation-success/$', views.confirmation_success, name='confirmation-success'),
    url(r'^finalize-order/(?P<orderid>\d+)/(?P<feedback>["0","1"]+)/$', views.finalize_order, name='finalize-order'),
    url(r'^wizard/$', views.wizard, name='wizard'),
    url(r'^welcome/$', views.welcome, name='welcome'),
    url(r'^bootcamp/$', views.bootcamp, name='bootcamp'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^edit-offer/(?P<offerid>\d+)/$', views.edit_offer, name='edit-offer'),
    url(r'^detail-offer/(?P<offerid>\d+)/$', views.detail_offer, name='detail-offer'),
    url(r'^accept-offer/(?P<orderid>\d+)/$', views.accept_offer, name='accept-offer'),
    url(r'^hire-offer/(?P<offerid>\d+)/$', views.hire_offer, name='hire-offer'),
    url(r'^edit-request/(?P<requestid>\d+)/$', views.edit_request, name='edit-request'),
    url(r'^detail-request/(?P<requestid>\d+)/$', views.detail_request, name='detail-request'),
    url(r'^accept-request/(?P<orderid>\d+)/$', views.accept_request, name='accept-request'),
    url(r'^hire-request/(?P<requestid>\d+)/$', views.hire_request, name='hire-request'),
    url(r'^community/(?P<comid>\d+)/$', views.index, name='indexcommunity'),
    url(r'^new-offer/$', views.edit_offer, name='new-offer'),
    url(r'^new-request/$', views.edit_request, name='new-request'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]
