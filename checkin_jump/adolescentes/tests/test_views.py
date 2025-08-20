import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from adolescentes.models import Adolescente, PequenoGrupo, Imperio, DiaEvento, Presenca


@pytest.fixture
def user_client(client):
    user = User.objects.create_user(username="viewer", password="pass")
    client.login(username="viewer", password="pass")
    return client


@pytest.mark.django_db
def test_listar_adolescentes_default_order(user_client):
    # Setup
    a1 = Adolescente.objects.create(nome="Ana", sobrenome="Silva", data_nascimento="2010-01-01")
    a2 = Adolescente.objects.create(nome="Ana", sobrenome="Almeida", data_nascimento="2011-01-01")
    # nome igual -> ordena por sobrenome secundário asc
    url = reverse("listar_adolescentes")
    resp = user_client.get(url)
    assert resp.status_code == 200
    content = resp.content.decode("utf-8")
    assert content.index("Ana Almeida") < content.index("Ana Silva")


@pytest.mark.django_db
def test_listar_adolescentes_filters_sem_pg_e_sem_imperio(user_client):
    pg = PequenoGrupo.objects.create(nome="PG X")
    imp = Imperio.objects.create(nome="Fogo")
    # um com tudo
    Adolescente.objects.create(nome="Joao", sobrenome="A", data_nascimento="2010-01-01", pg=pg, imperio=imp)
    # sem pg
    Adolescente.objects.create(nome="Maria", sobrenome="B", data_nascimento="2010-02-02", imperio=imp)
    # sem imperio
    Adolescente.objects.create(nome="Pedro", sobrenome="C", data_nascimento="2010-03-03", pg=pg)

    base = reverse("listar_adolescentes")

    # sem_pg
    r1 = user_client.get(base, {"pg": "sem_pg"})
    assert r1.status_code == 200
    html1 = r1.content.decode("utf-8")
    assert "Maria B" in html1 and "Joao A" not in html1

    # sem_imperio
    r2 = user_client.get(base, {"imperio": "sem_imperio"})
    assert r2.status_code == 200
    html2 = r2.content.decode("utf-8")
    assert "Pedro C" in html2 and "Joao A" not in html2


@pytest.mark.django_db
def test_listar_adolescentes_order_by_pg_and_imperio(user_client):
    pgA = PequenoGrupo.objects.create(nome="A PG")
    pgB = PequenoGrupo.objects.create(nome="B PG")
    impA = Imperio.objects.create(nome="A Imp")
    impB = Imperio.objects.create(nome="B Imp")
    Adolescente.objects.create(nome="Z", sobrenome="Z", data_nascimento="2010-01-01", pg=pgB, imperio=impB)
    Adolescente.objects.create(nome="A", sobrenome="A", data_nascimento="2010-01-01", pg=pgA, imperio=impA)

    url = reverse("listar_adolescentes")

    # ordenar por pg asc
    r_pg = user_client.get(url, {"ordenar_por": "pg", "direcao": "asc"})
    assert r_pg.status_code == 200
    html_pg = r_pg.content.decode("utf-8")
    # A PG vem antes de B PG
    assert html_pg.index("A A") < html_pg.index("Z Z")

    # ordenar por imperio desc -> B Imp antes de A Imp
    r_imp = user_client.get(url, {"ordenar_por": "imperio", "direcao": "desc"})
    assert r_imp.status_code == 200
    html_imp = r_imp.content.decode("utf-8")
    assert html_imp.index("Z Z") < html_imp.index("A A")


@pytest.mark.django_db
def test_checkin_dia_filters_and_post(user_client):
    dia = DiaEvento.objects.create(data=timezone.now().date())
    a1 = Adolescente.objects.create(nome="Ana", sobrenome="S", data_nascimento="2010-01-01")
    a2 = Adolescente.objects.create(nome="Bruno", sobrenome="S", data_nascimento="2010-01-01")

    # Marca um como presente
    Presenca.objects.create(dia=dia, adolescente=a1, presente=True)

    # filtro presentes
    url = reverse("checkin_dia", args=[dia.id])
    r_pres = user_client.get(url, {"filtro": "presentes"})
    assert r_pres.status_code == 200
    html_p = r_pres.content.decode("utf-8")
    assert "Ana S" in html_p and "Bruno S" not in html_p

    # filtro ausentes
    r_aus = user_client.get(url, {"filtro": "ausentes"})
    assert r_aus.status_code == 200
    html_a = r_aus.content.decode("utf-8")
    assert "Bruno S" in html_a and "Ana S" not in html_a

    # POST check-in: inverte presença
    resp_post = user_client.post(url, {"presentes": [str(a2.id)]})
    assert resp_post.status_code in (302, 200)
    a1_p = Presenca.objects.get(dia=dia, adolescente=a1)
    a2_p = Presenca.objects.get(dia=dia, adolescente=a2)
    assert a1_p.presente is False and a2_p.presente is True
