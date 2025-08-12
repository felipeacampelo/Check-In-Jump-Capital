from django.contrib import admin

from django.contrib import admin
from .models import Adolescente, DiaEvento, Presenca, PequenoGrupo, Imperio

from django import forms
from django.contrib import messages
from django.contrib.admin.helpers import ActionForm
from django.http import HttpResponse
import csv


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
    list_display = ("nome", "sobrenome", "pg", "imperio", "data_nascimento")
    search_fields = ("nome", "sobrenome", "pg__nome", "imperio__nome")
    list_filter = ("pg", "imperio", "genero")

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
    list_display = ("nome",)


@admin.register(Imperio)
class ImperioAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    list_display = ("nome",)

# Branding do painel
admin.site.site_header = "Check-in Jump — Admin"
admin.site.site_title = "Check-in Jump"
admin.site.index_title = "Painel de Administração"
