from django.contrib import admin

from django.urls import path, include

from django.contrib.auth import views as auth_views

from django.conf import settings

from django.conf.urls.static import static



urlpatterns = [

    path('admin/', admin.site.urls),

    path('', include('adolescentes.urls')),

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

