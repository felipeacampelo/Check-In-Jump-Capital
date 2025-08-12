import csv
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from adolescentes.models import Adolescente, PequenoGrupo, Imperio, DiaEvento, Presenca


@pytest.mark.django_db
def test_admin_bulk_define_pg_and_imperio(client: Client):
    # Create data
    pg1 = PequenoGrupo.objects.create(nome="PG A")
    pg2 = PequenoGrupo.objects.create(nome="PG B")
    imp1 = Imperio.objects.create(nome="Fogo")
    imp2 = Imperio.objects.create(nome="Água")

    a1 = Adolescente.objects.create(nome="Ana", sobrenome="Silva", data_nascimento="2010-01-01", pg=pg1, imperio=imp1)
    a2 = Adolescente.objects.create(nome="Bruno", sobrenome="Souza", data_nascimento="2010-02-02", pg=pg1, imperio=imp1)

    # Admin user and login
    admin_user = User.objects.create_superuser("admin", "admin@example.com", "pass")
    client.login(username="admin", password="pass")

    # Post action to change list
    url = reverse("admin:adolescentes_adolescente_changelist")
    data = {
        "action": "definir_pg_e_imperio",
        "select_across": 0,
        "index": 0,
        "pg": str(pg2.id),
        "imperio": str(imp2.id),
        "_selected_action": [str(a1.id), str(a2.id)],
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200

    a1.refresh_from_db()
    a2.refresh_from_db()
    assert a1.pg_id == pg2.id and a2.pg_id == pg2.id
    assert a1.imperio_id == imp2.id and a2.imperio_id == imp2.id


@pytest.mark.django_db
def test_admin_export_csv(client: Client):
    pg = PequenoGrupo.objects.create(nome="PG A")
    imp = Imperio.objects.create(nome="Fogo")
    Adolescente.objects.create(nome="Ana", sobrenome="Silva", data_nascimento="2010-01-01", pg=pg, imperio=imp)
    Adolescente.objects.create(nome="Bruno", sobrenome="Souza", data_nascimento="2010-02-02", pg=None, imperio=None)

    admin_user = User.objects.create_superuser("admin", "admin@example.com", "pass")
    client.login(username="admin", password="pass")

    url = reverse("admin:adolescentes_adolescente_changelist")
    ids = list(Adolescente.objects.values_list("id", flat=True))
    data = {
        "action": "exportar_csv",
        "select_across": 0,
        "index": 0,
        "_selected_action": [str(i) for i in ids],
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    content = response.content.decode("utf-8")
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    # Header + 2 rows
    assert rows[0] == ["Nome", "Sobrenome", "PG", "Império", "Data de Nascimento"]
    assert len(rows) == 3


@pytest.mark.django_db
def test_presenca_inline_visible_on_adolescente_change(client: Client):
    # Setup data
    a = Adolescente.objects.create(nome="Ana", sobrenome="Silva", data_nascimento="2010-01-01")
    d1 = DiaEvento.objects.create(data="2025-01-01")
    d2 = DiaEvento.objects.create(data="2025-01-08")
    Presenca.objects.create(adolescente=a, dia=d1, presente=True)
    Presenca.objects.create(adolescente=a, dia=d2, presente=False)

    admin_user = User.objects.create_superuser("admin", "admin@example.com", "pass")
    client.login(username="admin", password="pass")

    url = reverse("admin:adolescentes_adolescente_change", args=[a.id])
    response = client.get(url)
    assert response.status_code == 200
    # Inline fields present
    assert "Presenças" in response.content.decode("utf-8") or "Presenca" in response.content.decode("utf-8")
    assert "2010-01-01" not in response.content.decode("utf-8")  # ensure we didn't mix fields
