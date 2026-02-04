from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin, GroupAdmin as DjangoGroupAdmin
from .models import Adolescente, DiaEvento, Presenca, PequenoGrupo, Imperio

from django import forms
from django.contrib import messages
from django.contrib.admin.helpers import ActionForm
from django.http import HttpResponse
from django.template.response import TemplateResponse
import csv
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings


class PresencaInline(admin.TabularInline):
    model = Presenca
    extra = 0
    can_delete = False
    fields = ("dia", "presente")
    readonly_fields = ("dia", "presente")
    show_change_link = True
    ordering = ("-dia__data",)


class BulkUpdateAdolescenteActionForm(ActionForm):
    pg = forms.ModelChoiceField(
        queryset=PequenoGrupo.objects.all(), required=False, label="Definir PG"
    )
    imperio = forms.ModelChoiceField(
        queryset=Imperio.objects.all(), required=False, label="Definir Império"
    )


@admin.register(Adolescente)
class AdolescenteAdmin(admin.ModelAdmin):
    # Campos extras no topo da lista para ações em massa
    action_form = BulkUpdateAdolescenteActionForm

    # Barra de pesquisa e usabilidade
    list_display = ("nome", "sobrenome", "pg", "imperio", "data_nascimento", "ano")
    search_fields = ("nome", "sobrenome", "pg__nome", "imperio__nome")
    list_filter = ("ano", "pg", "imperio", "genero")

    # Prioridades: ordenação, paginação e performance
    ordering = ("nome", "sobrenome")
    list_per_page = 50
    save_on_top = True
    save_as = True
    list_select_related = ("pg", "imperio")

    # Autocomplete de FKs (requer search nos admins relacionados)
    autocomplete_fields = ["pg", "imperio"]

    inlines = [PresencaInline]

    actions = [
        "definir_pg",
        "definir_imperio",
        "definir_pg_e_imperio",
        "exportar_csv",
    ]

    @admin.action(description="Definir PG para selecionados")
    def definir_pg(self, request, queryset):
        pg_id = request.POST.get("pg")
        if not pg_id:
            self.message_user(
                request,
                "Nenhum PG selecionado no formulário de ações.",
                level=messages.WARNING,
            )
            return
        updated = queryset.update(pg=pg_id)
        self.message_user(request, f"PG definido para {updated} registros.")

    @admin.action(description="Definir Império para selecionados")
    def definir_imperio(self, request, queryset):
        imperio_id = request.POST.get("imperio")
        if not imperio_id:
            self.message_user(
                request,
                "Nenhum Império selecionado no formulário de ações.",
                level=messages.WARNING,
            )
            return
        updated = queryset.update(imperio=imperio_id)
        self.message_user(request, f"Império definido para {updated} registros.")

    @admin.action(description="Definir PG e Império para selecionados")
    def definir_pg_e_imperio(self, request, queryset):
        pg_id = request.POST.get("pg")
        imperio_id = request.POST.get("imperio")

        if not pg_id and not imperio_id:
            self.message_user(
                request,
                "Selecione ao menos um valor (PG ou Império) no formulário de ações.",
                level=messages.WARNING,
            )
            return

        data = {}
        if pg_id:
            data["pg"] = pg_id
        if imperio_id:
            data["imperio"] = imperio_id
        updated = queryset.update(**data)
        self.message_user(request, f"Atualização em massa aplicada a {updated} registros.")

    @admin.action(description="Exportar CSV (nome, sobrenome, PG, Império, nascimento)")
    def exportar_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="adolescentes.csv"'
        writer = csv.writer(response)
        writer.writerow(["Nome", "Sobrenome", "PG", "Império", "Data de Nascimento"])
        for a in queryset.select_related("pg", "imperio"):
            writer.writerow([
                a.nome,
                a.sobrenome,
                a.pg.nome if a.pg else "",
                a.imperio.nome if a.imperio else "",
                a.data_nascimento.strftime("%Y-%m-%d") if a.data_nascimento else "",
            ])
        return response

admin.site.register(DiaEvento)
admin.site.register(Presenca)
@admin.register(PequenoGrupo)
class PequenoGrupoAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    list_display = ("nome", "ano")
    list_filter = ("ano",)


@admin.register(Imperio)
class ImperioAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    list_display = ("nome", "ano")
    list_filter = ("ano",)

# Branding do painel
admin.site.site_header = "Check-in Jump — Admin"
admin.site.site_title = "Check-in Jump"
admin.site.index_title = "Painel de Administração"


# --- User admin: gerar links de definição de senha ---
def build_base_url(request):
    # Prioriza SITE_URL nas settings, se configurado (ex.: https://seu-dominio.railway.app)
    site_url = getattr(settings, 'SITE_URL', None)
    if site_url:
        return site_url.rstrip('/')
    # Fallback: host do request atual
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    return f"{scheme}://{host}"


@admin.action(description="Gerar links de definir senha (CSV)")
def gerar_links_definir_senha(modeladmin, request, queryset):
    """Gera um CSV com: username, email, link de definição de senha.
    O link usa a rota 'password_reset_confirm' com uidb64 e token padrão do Django.
    """
    base_url = build_base_url(request)

    rows = [("username", "email", "definir_senha_link")]
    for user in queryset:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        link = f"{base_url}{path}"
        rows.append((user.username, user.email or "", link))

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="links_definir_senha.csv"'
    writer = csv.writer(response)
    writer.writerows(rows)
    return response


class UserAdmin(DjangoUserAdmin):
    # Facilita ações em massa e visualização
    actions = [gerar_links_definir_senha]
    list_filter = DjangoUserAdmin.list_filter + ('groups',)
    search_fields = DjangoUserAdmin.search_fields + ('groups__name',)
    # Garante UI amigável para grupos/permissões
    filter_horizontal = ('groups', 'user_permissions')


class AtribuirGrupoActionForm(ActionForm):
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(), required=False, label="Selecione um grupo"
    )


# Adiciona ações em massa para vincular/desvincular usuários de um grupo
UserAdmin.action_form = AtribuirGrupoActionForm

@admin.action(description="Adicionar usuários selecionados ao grupo informado")
def adicionar_ao_grupo(modeladmin, request, queryset):
    grupo = request.POST.get('grupo')
    if not grupo:
        modeladmin.message_user(request, "Nenhum grupo selecionado no formulário de ações.", level=messages.WARNING)
        return
    try:
        g = Group.objects.get(pk=grupo)
    except Group.DoesNotExist:
        modeladmin.message_user(request, "Grupo inválido.", level=messages.ERROR)
        return
    count = 0
    for user in queryset:
        user.groups.add(g)
        count += 1
    modeladmin.message_user(request, f"{count} usuário(s) adicionados ao grupo '{g.name}'.")


@admin.action(description="Remover usuários selecionados do grupo informado")
def remover_do_grupo(modeladmin, request, queryset):
    grupo = request.POST.get('grupo')
    if not grupo:
        modeladmin.message_user(request, "Nenhum grupo selecionado no formulário de ações.", level=messages.WARNING)
        return
    try:
        g = Group.objects.get(pk=grupo)
    except Group.DoesNotExist:
        modeladmin.message_user(request, "Grupo inválido.", level=messages.ERROR)
        return
    count = 0
    for user in queryset:
        user.groups.remove(g)
        count += 1
    modeladmin.message_user(request, f"{count} usuário(s) removidos do grupo '{g.name}'.")


# Anexa as novas ações ao UserAdmin existente
UserAdmin.actions = list(UserAdmin.actions) + [adicionar_ao_grupo, remover_do_grupo]


# --- Group admin: gerenciar membros diretamente ---
class UserGroupInline(admin.TabularInline):
    model = User.groups.through  # Tabela M2M
    extra = 1
    verbose_name = "Membro"
    verbose_name_plural = "Membros do grupo"
    autocomplete_fields = ['user']
    # Evita editar o próprio campo group (fixado pela página do Group)
    can_delete = True


class CustomGroupAdmin(DjangoGroupAdmin):
    inlines = [UserGroupInline]
    search_fields = ('name', 'user__username', 'user__first_name', 'user__last_name')
    filter_horizontal = ('permissions',)


@admin.action(description="Mostrar links de definir senha na tela")
def mostrar_links_na_tela(modeladmin, request, queryset):
    base_url = build_base_url(request)
    items = []
    for user in queryset:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        link = f"{base_url}{path}"
        items.append({
            'username': user.username,
            'email': user.email or "",
            'link': link,
            'full_name': user.get_full_name() or user.username,
        })

    context = {
        **modeladmin.admin_site.each_context(request),
        'title': 'Links para definir senha',
        'items': items,
        'queryset_count': queryset.count(),
    }
    return TemplateResponse(request, 'admin/definir_senha_links.html', context)


 


# Substitui o admin padrão do User para incluir a action
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)
UserAdmin.actions = list(UserAdmin.actions) + [mostrar_links_na_tela]

# Substitui o Group admin para incluir os membros inline
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass
admin.site.register(Group, CustomGroupAdmin)

