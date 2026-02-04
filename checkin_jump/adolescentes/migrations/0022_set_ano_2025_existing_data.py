from django.db import migrations


def set_ano_2025(apps, schema_editor):
    """Seta ano=2025 para todos os registros existentes"""
    PequenoGrupo = apps.get_model('adolescentes', 'PequenoGrupo')
    Imperio = apps.get_model('adolescentes', 'Imperio')
    Adolescente = apps.get_model('adolescentes', 'Adolescente')
    DiaEvento = apps.get_model('adolescentes', 'DiaEvento')
    
    # Atualizar todos os registros existentes para ano=2025
    PequenoGrupo.objects.filter(ano=2026).update(ano=2025)
    Imperio.objects.filter(ano=2026).update(ano=2025)
    Adolescente.objects.filter(ano=2026).update(ano=2025)
    DiaEvento.objects.filter(ano=2026).update(ano=2025)


def reverse_set_ano(apps, schema_editor):
    """Reverte para ano=2026 (operação reversa)"""
    PequenoGrupo = apps.get_model('adolescentes', 'PequenoGrupo')
    Imperio = apps.get_model('adolescentes', 'Imperio')
    Adolescente = apps.get_model('adolescentes', 'Adolescente')
    DiaEvento = apps.get_model('adolescentes', 'DiaEvento')
    
    PequenoGrupo.objects.filter(ano=2025).update(ano=2026)
    Imperio.objects.filter(ano=2025).update(ano=2026)
    Adolescente.objects.filter(ano=2025).update(ano=2026)
    DiaEvento.objects.filter(ano=2025).update(ano=2026)


class Migration(migrations.Migration):

    dependencies = [
        ('adolescentes', '0021_add_ano_and_new_fields'),
    ]

    operations = [
        migrations.RunPython(set_ano_2025, reverse_set_ano),
    ]
