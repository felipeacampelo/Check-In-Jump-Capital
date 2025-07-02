from django.urls import path
from . import views
from .views import login_view, logout_view, listar_adolescentes
from .views import exportar_adolescentes_csv, exportar_presencas_csv

urlpatterns = [
    # Autenticação
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Página inicial (escolha uma)
    path("", views.lista_dias_evento, name="pagina_checkin"),

    # Adolescentes
    path("adolescentes/", listar_adolescentes, name="listar_adolescentes"),
    path("adolescentes/novo/", views.criar_adolescente, name="criar_adolescente"),
    path("adolescentes/editar/<int:id>/", views.editar_adolescente, name="editar_adolescente"),
    path("adolescentes/excluir/<int:id>/", views.excluir_adolescente, name="excluir_adolescente"),

    # Check-in
    path("checkin/", views.lista_dias_evento, name="pagina_checkin"),
    path("checkin/novo-dia/", views.adicionar_dia_evento, name="novo_dia_evento"),
    path("checkin/<int:dia_id>/", views.checkin_dia, name="checkin_dia"),
    path('atualizar-presenca/', views.atualizar_presenca, name='atualizar_presenca'),

    # PGs
    path('pgs/', views.lista_pgs, name='lista_pgs'),
    path('pgs/adicionar/', views.adicionar_pg, name='adicionar_pg'),
    path('pgs/<int:pg_id>/', views.detalhes_pg, name='detalhes_pg'),

    #Exportar CSV
    path('exportar/adolescentes/', exportar_adolescentes_csv, name='exportar_adolescentes_csv'),
    path('exportar/presencas/', exportar_presencas_csv, name='exportar_presencas_csv'),
]

