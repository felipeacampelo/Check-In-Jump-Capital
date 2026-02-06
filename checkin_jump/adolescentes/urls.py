from django.urls import path
from . import views
from .views import login_view, logout_view, listar_adolescentes
from .views import exportar_adolescentes_csv, exportar_presencas_csv, selecionar_dia_exportar

urlpatterns = [
    # Autenticação
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    
    # Seletor de Ano
    path("ano/<int:ano>/", views.trocar_ano, name="trocar_ano"),

    # Página inicial (escolha uma)
    path("", views.lista_dias_evento, name="pagina_checkin"),

    # Adolescentes
    path("adolescentes/", listar_adolescentes, name="listar_adolescentes"),
    path("adolescentes/novo/", views.criar_adolescente, name="criar_adolescente"),
    path("adolescentes/editar/<int:id>/", views.editar_adolescente, name="editar_adolescente"),
    path("adolescentes/excluir/<int:id>/", views.excluir_adolescente, name="excluir_adolescente"),
    path("ajax/form/<int:adolescente_id>/", views.get_form_ajax, name="get_form_ajax"),

    # Check-in
    path("checkin/", views.lista_dias_evento, name="pagina_checkin"),
    path("checkin/novo-dia/", views.adicionar_dia_evento, name="novo_dia_evento"),
    path("checkin/<int:dia_id>/", views.checkin_dia, name="checkin_dia"),
    path('atualizar-presenca/', views.atualizar_presenca, name='atualizar_presenca'),
    path("checkin/<int:dia_id>/pg-vip/", views.pg_vip, name="pg_vip"),

    # PGs
    path('pgs/', views.lista_pgs, name='lista_pgs'),
    path('pgs/adicionar/', views.adicionar_pg, name='adicionar_pg'),
    path('pgs/<int:pg_id>/', views.detalhes_pg, name='detalhes_pg'),
    path('pgs/<int:pg_id>/bulk-add/', views.bulk_add_pg, name='bulk_add_pg'),
    path('pgs/<int:pg_id>/bulk-remove/', views.bulk_remove_pg, name='bulk_remove_pg'),

    # Impérios
    path('imperios/', views.lista_imperios, name='lista_imperios'),
    path('imperios/adicionar/', views.adicionar_imperio, name='adicionar_imperio'),
    path('imperios/<int:imperio_id>/', views.detalhes_imperio, name='detalhes_imperio'),
    path('imperios/<int:imperio_id>/bulk-add/', views.bulk_add_imperio, name='bulk_add_imperio'),
    path('imperios/<int:imperio_id>/bulk-remove/', views.bulk_remove_imperio, name='bulk_remove_imperio'),

    #Exportar CSV
    path('exportar/adolescentes/', exportar_adolescentes_csv, name='exportar_adolescentes_csv'),
    path('exportar/presencas/', exportar_presencas_csv, name='exportar_presencas_csv'),
    path('exportar/presencas/selecionar-dia/', selecionar_dia_exportar, name='selecionar_dia_exportar'),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Contagem de Auditório
    path('contagem-auditorio/', views.contagem_auditorio, name='contagem_auditorio'),

    # Duplicados (apenas com permissão review_duplicates)
    path('adolescentes/duplicados/sugestoes/', views.sugestoes_duplicados, name='sugestoes_duplicados'),
    path('adolescentes/duplicados/merge/', views.merge_duplicados, name='merge_duplicados'),
    path('adolescentes/duplicados/rejeitar/', views.rejeitar_duplicado, name='rejeitar_duplicado'),
]

