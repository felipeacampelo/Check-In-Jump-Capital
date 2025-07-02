from datetime import date, datetime
from django.shortcuts import render, get_object_or_404, redirect
from .models import Adolescente, DiaEvento, Presenca, PequenoGrupo, Imperio
from .forms import AdolescenteForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, Avg, F
import json

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect("listar_adolescentes")  # Redireciona para a lista após login
        else:
            messages.error(request, "Usuário ou senha inválidos. Por favor, verifique suas credenciais e tente novamente.")

    return render(request, "adolescentes/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")  # Redireciona para a tela de login após logout

@login_required
def listar_adolescentes(request):
    adolescentes = Adolescente.objects.all()
    total_adolescentes = adolescentes.count()

    # Filtros
    pg_id = request.GET.get('pg')
    genero = request.GET.get('genero')
    imperio_id = request.GET.get('imperio')
    busca = request.GET.get('busca')

    if busca:
        adolescentes = adolescentes.filter(nome__icontains=busca)
    if pg_id:
        adolescentes = adolescentes.filter(pg_id=pg_id)
    if genero:
        adolescentes = adolescentes.filter(genero=genero)
    if imperio_id:
        adolescentes = adolescentes.filter(imperio_id=imperio_id)

    # 🔧 Adicione os dados necessários para os filtros aparecerem
    pgs = PequenoGrupo.objects.all()
    imperios = Imperio.objects.all()

    return render(request, 'adolescentes/listar.html', {
        'adolescentes': adolescentes,
        'total_adolescentes': total_adolescentes,
        'pgs': pgs,
        'imperios': imperios,
    })

@login_required
def pagina_checkin(request):
    return render(request, 'checkin.html')

@login_required
def pagina_pgs(request):
    return render(request, 'pgs.html')

@login_required
def criar_adolescente(request):
    if request.method == "POST":
        form = AdolescenteForm(request.POST, request.FILES)
        if form.is_valid():
            # Verifica se a data de nascimento não é futura
            data_nascimento = form.cleaned_data['data_nascimento']
            if data_nascimento > datetime.now().date():
                messages.error(request, "A data de nascimento não pode ser no futuro.")
                return redirect('criar_adolescente')

            form.save()
            return redirect('listar_adolescentes')
    else:
        form = AdolescenteForm()
    return render(request, 'adolescentes/criar_adolescente.html', {'form': form})

@login_required
def editar_adolescente(request, id):
    adolescente = get_object_or_404(Adolescente, id=id)
    if request.method == "POST":
        form = AdolescenteForm(request.POST, request.FILES, instance=adolescente)
        if form.is_valid():
            form.save()
            return redirect('listar_adolescentes')
    else:
        form = AdolescenteForm(instance=adolescente)
    return render(request, 'adolescentes/criar_adolescente.html', {'form': form})

@login_required
def excluir_adolescente(request, id):
    adolescente = get_object_or_404(Adolescente, id=id)
    if request.method == "POST":
        adolescente.delete()
        return redirect('listar_adolescentes')
    return render(request, 'adolescentes/confirmar_exclusao.html', {'adolescente': adolescente})

@login_required
def lista_dias_evento(request):
    dias = DiaEvento.objects.annotate(
        total_presentes=Count('presenca', filter=Q(presenca__presente=True))
    ).order_by('-data')

    if dias.exists():
        soma_presentes = sum(dia.total_presentes for dia in dias)
        media_presentes = soma_presentes / len(dias)
    else:
        media_presentes = 0

    return render(request, 'checkin/lista_dias.html', {
        'dias': dias,
        'media_presentes': media_presentes,
    })


@login_required
@permission_required('checkin.add_diaevento', raise_exception=True)
def adicionar_dia_evento(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        if DiaEvento.objects.filter(data=data).exists():
            messages.warning(request, "Esse dia já foi adicionado.")
        if data and datetime.strptime(data, "%Y-%m-%d").date() < date.today():
            messages.warning(request, "Não é possível adicionar um dia no passado.")
        else:
            DiaEvento.objects.create(data=data)
        return redirect('pagina_checkin')
    return render(request, 'checkin/adicionar_dia.html')

@login_required
def checkin_dia(request, dia_id):
    dia = get_object_or_404(DiaEvento, pk=dia_id)
    adolescentes = Adolescente.objects.all()
    filtro = request.GET.get('filtro', 'todos')  # padrão: todos

    presencas = Presenca.objects.filter(dia=dia)
    presentes_ids = presencas.filter(presente=True).values_list('adolescente_id', flat=True)

    # Aplica filtro
    if filtro == 'presentes':
        adolescentes = adolescentes.filter(id__in=presentes_ids)
    elif filtro == 'ausentes':
        adolescentes = adolescentes.exclude(id__in=presentes_ids)

    # Ordena: primeiro os presentes
    adolescentes = sorted(adolescentes, key=lambda x: x.id not in presentes_ids)

    if request.method == 'POST':
        presencas_ids = request.POST.getlist('presentes')
        Presenca.objects.filter(dia=dia).delete()
        for adol in adolescentes:
            Presenca.objects.create(
                adolescente=adol,
                dia=dia,
                presente=str(adol.id) in presencas_ids
            )
        messages.success(request, "Check-in realizado com sucesso!")
        return redirect('checkin_dia', dia_id=dia.id)

    return render(request, 'checkin/checkin_dia.html', {
        'dia': dia,
        'adolescentes': adolescentes,
        'presentes_ids': presentes_ids,
        'filtro': filtro,
    })

@login_required
@require_http_methods(["POST"])
def atualizar_presenca(request):
    try:
        # Parse do JSON enviado pelo JavaScript
        data = json.loads(request.body)
        adolescente_id = data.get('adolescente_id')
        dia_id = data.get('dia_id')
        presente = data.get('presente')
        
        # Validação dos dados
        if not all([adolescente_id, dia_id, presente is not None]):
            return JsonResponse({
                'error': 'Dados incompletos'
            }, status=400)
        
        # Busca os objetos
        adolescente = get_object_or_404(Adolescente, id=adolescente_id)
        dia = get_object_or_404(DiaEvento, id=dia_id)
        
        # Atualiza ou cria a presença
        presenca, created = Presenca.objects.update_or_create(
            adolescente=adolescente,
            dia=dia,
            defaults={'presente': presente}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Presença atualizada com sucesso',
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
def adicionar_pg(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        lider = request.POST.get('lider')

        if nome:
            PequenoGrupo.objects.create(nome=nome, lider=lider)
            messages.success(request, "PG criado com sucesso.")
            return redirect('lista_pgs')
        else:
            messages.error(request, "O nome do PG é obrigatório.")

    return render(request, 'pgs/adicionar_pg.html')

@login_required
def lista_pgs(request):
    pgs = PequenoGrupo.objects.all()
    return render(request, 'pgs/lista_pgs.html', {'pgs': pgs})

@login_required
def detalhes_pg(request, pg_id):
    pg = get_object_or_404(PequenoGrupo, id=pg_id)
    adolescentes = Adolescente.objects.filter(pg=pg)
    return render(request, 'pgs/pg.html', {'pg': pg, 'adolescentes': adolescentes})
