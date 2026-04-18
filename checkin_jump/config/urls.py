from django.contrib import admin

from django.urls import path, include

from django.contrib.auth import views as auth_views

from django.conf import settings

from django.conf.urls.static import static

from django.views.generic import RedirectView


ICON_URL = settings.STATIC_URL + 'adolescentes/img/favicon.ico'
APPLE_ICON_URL = settings.STATIC_URL + 'adolescentes/img/apple-touch-icon.png'


urlpatterns = [

    path('admin/', admin.site.urls),

    path('', include('adolescentes.urls')),

    path('favicon.ico', RedirectView.as_view(url=ICON_URL, permanent=False)),
    path('apple-touch-icon.png', RedirectView.as_view(url=APPLE_ICON_URL, permanent=False)),
    path('apple-touch-icon-precomposed.png', RedirectView.as_view(url=APPLE_ICON_URL, permanent=False)),
    path('apple-touch-icon-120x120.png', RedirectView.as_view(url=APPLE_ICON_URL, permanent=False)),
    path('apple-touch-icon-120x120-precomposed.png', RedirectView.as_view(url=APPLE_ICON_URL, permanent=False)),

    # Links para definir senha via token (usados pelos links gerados no admin)

    path(

        'accounts/reset/<uidb64>/<token>/',

        auth_views.PasswordResetConfirmView.as_view(

            template_name='adolescentes/auth/password_reset_confirm.html'

        ),

        name='password_reset_confirm'

    ),

    path(

        'accounts/reset/done/',

        auth_views.PasswordResetCompleteView.as_view(

            template_name='adolescentes/auth/password_reset_complete.html'

        ),

        name='password_reset_complete'

    ),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# Debug Toolbar URLs (apenas em desenvolvimento)

if settings.DEBUG:

    import debug_toolbar

    urlpatterns = [

        path('__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns

