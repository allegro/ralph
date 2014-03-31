from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from ralph.business.views import Index

urlpatterns = patterns('',
                       url(r'^venture-grid/$',
                           'ralph.business.views.venture_grid'),
                       url(r'^price-grid/$',
                           'ralph.business.views.price_grid'),
                       url(r'^summary-grid/$',
                           'ralph.business.views.summary_grid'),
                       url(r'^detail-grid/$',
                           'ralph.business.views.detail_grid'),
                       url(r'^summary-pie/$',
                           'ralph.business.views.summary_pie'),
                       url(r'^history/$', 'ralph.business.views.history'),
                       url(r'^csv/$', 'ralph.business.views.csv'),
                       (r'^$', login_required(Index.as_view())),
                       )
