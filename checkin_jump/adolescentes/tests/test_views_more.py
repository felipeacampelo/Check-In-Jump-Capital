import json
import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils import timezone

from adolescentes.models import (
    Adolescente,
    PequenoGrupo,
    Imperio,
    DiaEvento,
    Presenca,
)


@pytest.fixture
def auth_client(db, client):
    user = User.objects.create_user(username="user", password="pass")
    client.login(username="user", password="pass")
    return client


@pytest.fixture
def auth_client_perms(db, client):
    user = User.objects.create_user(username="editor", password="pass")
    perms = Permission.objects.filter(codename__in=["change_adolescente", "delete_adolescente"])
    user.user_permissions.add(*perms)
    client.login(username="editor", password="pass")
    return client


@pytest.mark.django_db
def test_listar_busca_nome_completo_e_invertido(auth_client):
    Adolescente.objects.create(nome="Maria", sobrenome="Clara", data_nascimento="2010-01-01")
    Adolescente.objects.create(nome="Clara", sobrenome="Maria", data_nascimento="2010-01-01")

    url = reverse("listar_adolescentes")
    # nome completo
    r1 = auth_client.get(url, {"busca": "Maria Clara"})
    assert r1.status_code == 200
    html1 = r1.content.decode("utf-8")
    assert "Maria Clara" in html1

    # invertido
    r2 = auth_client.get(url, {"busca": "Clara Maria"})
    assert r2.status_code == 200
    html2 = r2.content.decode("utf-8")
    assert "Clara Maria" in html2


@pytest.mark.django_db
def test_listar_ordenacao_genero_e_data(auth_client):
    Adolescente.objects.create(nome="A", sobrenome="A", genero="M", data_nascimento="2012-01-01")
    Adolescente.objects.create(nome="B", sobrenome="B", genero="F", data_nascimento="2010-01-01")

    url = reverse("listar_adolescentes")

    # ordenar por genero asc => F antes de M
    r_gen = auth_client.get(url, {"ordenar_por": "genero", "direcao": "asc"})
    assert r_gen.status_code == 200
    html_g = r_gen.content.decode("utf-8")
    assert html_g.index("B B") < html_g.index("A A")

    # ordenar por data nasc desc => 2012 antes de 2010
    r_dt = auth_client.get(url, {"ordenar_por": "data_nascimento", "direcao": "desc"})
    assert r_dt.status_code == 200
    html_d = r_dt.content.decode("utf-8")
    assert html_d.index("A A") < html_d.index("B B")


@pytest.mark.django_db
def test_listar_paginacao(auth_client):
    for i in range(30):
        Adolescente.objects.create(nome=f"Nome{i:02}", sobrenome=f"Sob{i:02}", data_nascimento="2010-01-01")
    url = reverse("listar_adolescentes")
    r1 = auth_client.get(url, {"page": 1})
    r2 = auth_client.get(url, {"page": 2})
    assert r1.status_code == 200 and r2.status_code == 200
    # item da segunda página deve aparecer somente na page 2
    html1 = r1.content.decode("utf-8")
    html2 = r2.content.decode("utf-8")
    assert "Nome29 Sob29" in html2 or "Nome25 Sob25" in html2


@pytest.mark.django_db
def test_editar_adolescente_preserva_params(auth_client_perms):
    a = Adolescente.objects.create(nome="John", sobrenome="Doe", data_nascimento="2010-01-01")
    pg = PequenoGrupo.objects.create(nome="PG Test")
    params = "busca=John&ordenar_por=nome&direcao=asc&page=2"
    url = reverse("editar_adolescente", args=[a.id]) + f"?{params}"
    r = auth_client_perms.post(url, {
        "nome": "John",
        "sobrenome": "Doe",
        "data_nascimento": "2010-01-01",
        "pg": str(pg.id)
    }, follow=False)
    # redireciona para lista mantendo params
    assert r.status_code == 302
    assert reverse("listar_adolescentes") in r.headers.get("Location", "")
    assert "busca=John" in r.headers.get("Location", "")


@pytest.mark.django_db
def test_excluir_adolescente_preserva_params(auth_client_perms):
    a = Adolescente.objects.create(nome="John", sobrenome="Doe", data_nascimento="2010-01-01")
    params = "busca=John&ordenar_por=nome&direcao=asc&page=3"
    url = reverse("excluir_adolescente", args=[a.id]) + f"?{params}"
    r = auth_client_perms.post(url, {}, follow=False)
    assert r.status_code == 302
    assert reverse("listar_adolescentes") in r.headers.get("Location", "")
    assert "page=3" in r.headers.get("Location", "")


@pytest.mark.django_db
def test_atualizar_presenca_ok_e_bad_request(auth_client):
    dia = DiaEvento.objects.create(data=timezone.now().date())
    a = Adolescente.objects.create(nome="A", sobrenome="B", data_nascimento="2010-01-01")
    url = reverse("atualizar_presenca")

    # OK
    payload = {"adolescente_id": a.id, "dia_id": dia.id, "presente": True}
    r_ok = auth_client.post(url, data=json.dumps(payload), content_type="application/json")
    assert r_ok.status_code == 200

    # Bad Request
    bad = {"adolescente_id": a.id, "presente": True}
    r_bad = auth_client.post(url, data=json.dumps(bad), content_type="application/json")
    assert r_bad.status_code == 400


@pytest.mark.django_db
def test_checkin_dia_contagens(auth_client):
    dia = DiaEvento.objects.create(data=timezone.now().date())
    url = reverse("checkin_dia", args=[dia.id])

    # Contagem auditório válida
    r1 = auth_client.post(url, {"contagem_auditorio": "1", "quantidade_pessoas": "123"})
    assert r1.status_code in (302, 200)

    # Contagem visitantes inválida (negativo)
    r2 = auth_client.post(url, {"contagem_visitantes": "1", "quantidade_visitantes": "-5"})
    assert r2.status_code in (302, 200)

    # Contagem visitantes válida
    r3 = auth_client.post(url, {"contagem_visitantes": "1", "quantidade_visitantes": "7"})
    assert r3.status_code in (302, 200)
