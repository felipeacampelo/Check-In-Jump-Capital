from datetime import date, datetime
from django.shortcuts import render, get_object_or_404, redirect
from .models import Adolescente, DiaEvento, Presenca, PequenoGrupo, Imperio, ContagemAuditorio
from .forms import AdolescenteForm, DiaEventoForm, ContagemAuditorioForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, Avg, F, Case, When, Value
from django.db.models import Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv
from django.http import HttpResponse

import json
from django.urls import reverse
from urllib.parse import urlencode

def buscar_adolescentes_por_nome(queryset, termo_busca):
    """
    Função auxiliar para buscar adolescentes por nome de forma mais inteligente
    """
    if not termo_busca:
        return queryset
    
    # Remove espaços extras e divide em palavras
    palavras = [palavra.strip() for palavra in termo_busca.split() if palavra.strip()]
    
    if not palavras:
        return queryset
    
    if len(palavras) == 1:
        # Busca simples: uma palavra em nome ou sobrenome
        return queryset.filter(
            Q(nome__icontains=palavras[0]) | Q(sobrenome__icontains=palavras[0])
        )
    else:
        # Busca por nome completo: múltiplas estratégias
        # 1. Busca por nome completo concatenado
        nome_completo = ' '.join(palavras)
        query = Q()
        
        # 2. Busca por nome completo concatenado (nome + sobrenome)
        query |= Q(nome__icontains=nome_completo)
        query |= Q(sobrenome__icontains=nome_completo)
        
        # 3. Busca por nome completo concatenado (sobrenome + nome)
        nome_invertido = ' '.join(palavras[::-1])
        query |= Q(nome__icontains=nome_invertido)
        query |= Q(sobrenome__icontains=nome_invertido)
        
        # 4. Busca por todas as palavras em nome ou sobrenome
        query_palavras = Q()
        for palavra in palavras:
            query_palavras &= (Q(nome__icontains=palavra) | Q(sobrenome__icontains=palavra))
        query |= query_palavras
        
        return queryset.filter(query)

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
    busca = request.GET.get('busca', '')
    pg_id = request.GET.get('pg')
    genero = request.GET.get('genero')
    imperio_id = request.GET.get('imperio')
    
    # Parâmetros de ordenação
    ordenar_por = request.GET.get('ordenar_por', 'nome')  # Padrão: ordenar por nome
    direcao = request.GET.get('direcao', 'asc')  # Padrão: ascendente

    adolescentes = Adolescente.objects.all()
    if busca:
        adolescentes = buscar_adolescentes_por_nome(adolescentes, busca)
    if pg_id:
        adolescentes = adolescentes.filter(pg__id=pg_id)
    if genero:
        adolescentes = adolescentes.filter(genero=genero)
    if imperio_id:
        adolescentes = adolescentes.filter(imperio__id=imperio_id)

    # Aplicar ordenação
    if ordenar_por == 'nome':
        adolescentes = adolescentes.order_by('nome' if direcao == 'asc' else '-nome')
    elif ordenar_por == 'sobrenome':
        adolescentes = adolescentes.order_by('sobrenome' if direcao == 'asc' else '-sobrenome')
    elif ordenar_por == 'genero':
        adolescentes = adolescentes.order_by('genero' if direcao == 'asc' else '-genero')
    elif ordenar_por == 'data_nascimento':
        adolescentes = adolescentes.order_by('data_nascimento' if direcao == 'asc' else '-data_nascimento')
    elif ordenar_por == 'pg':
        adolescentes = adolescentes.order_by('pg__nome' if direcao == 'asc' else '-pg__nome')
    elif ordenar_por == 'imperio':
        adolescentes = adolescentes.order_by('imperio__nome' if direcao == 'asc' else '-imperio__nome')
    else:
        # Padrão: ordenar por nome
        adolescentes = adolescentes.order_by('nome')

    total_adolescentes = adolescentes.count()
    pgs = PequenoGrupo.objects.all()
    imperios = Imperio.objects.all()

    # Pré-carrega presenças para cada adolescente
    adolescentes = adolescentes.prefetch_related(
        Prefetch('presenca_set', queryset=Presenca.objects.select_related('dia').order_by('-dia__data'))
    )

    # Paginação
    paginator = Paginator(adolescentes, 25)  # 25 registros por página
    page = request.GET.get('page')
    
    try:
        adolescentes_paginados = paginator.page(page)
    except PageNotAnInteger:
        # Se a página não for um número, mostrar a primeira página
        adolescentes_paginados = paginator.page(1)
    except EmptyPage:
        # Se a página estiver fora do range, mostrar a última página
        adolescentes_paginados = paginator.page(paginator.num_pages)

    # Anexa um formulário de edição para cada adolescente na página atual
    for adolescente in adolescentes_paginados:
        setattr(adolescente, 'form_edicao', AdolescenteForm(instance=adolescente))

    return render(request, 'adolescentes/listar.html', {
        'adolescentes': adolescentes_paginados,
        'total_adolescentes': total_adolescentes,
        'pgs': pgs,
        'imperios': imperios,
        'busca': busca,
        'pg_selecionado': pg_id,
        'genero_selecionado': genero,
        'imperio_selecionado': imperio_id,
        'ordenar_por': ordenar_por,
        'direcao': direcao
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

@permission_required('adolescentes.change_adolescente', raise_exception=True)
@login_required
def editar_adolescente(request, id):
    adolescente = get_object_or_404(Adolescente, id=id)
    if request.method == "POST":
        form = AdolescenteForm(request.POST, request.FILES, instance=adolescente)
        if form.is_valid():
            form.save()
            messages.success(request, "Adolescente atualizado com sucesso.")
        else:
            messages.error(request, "Não foi possível salvar. Verifique os campos e tente novamente.")
        # Redireciona mantendo filtros, busca e página
        params = request.GET.urlencode() or request.POST.get('params', '')
        url = reverse('listar_adolescentes')
        if params:
            url = f"{url}?{params}"
        return redirect(url)
    # Em GET, direciona para a lista
    return redirect('listar_adolescentes')

@permission_required('adolescentes.delete_adolescente', raise_exception=True)
@login_required
def excluir_adolescente(request, id):
    adolescente = get_object_or_404(Adolescente, id=id)
    if request.method == "POST":
        adolescente.delete()
        messages.success(request, "Adolescente excluído com sucesso.")
        # Redireciona mantendo filtros, busca e página
        params = request.GET.urlencode() or request.POST.get('params', '')
        url = reverse('listar_adolescentes')
        if params:
            url = f"{url}?{params}"
        return redirect(url)
    # Em GET, direciona para a lista
    return redirect('listar_adolescentes')

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
        form = DiaEventoForm(request.POST)
        if form.is_valid():
            if DiaEvento.objects.filter(data=form.cleaned_data['data']).exists():
                messages.warning(request, "Esse dia já foi adicionado.")
            else:
                form.save()
                messages.success(request, "Evento criado com sucesso!")
            return redirect('pagina_checkin')
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        form = DiaEventoForm()
    
    return render(request, 'checkin/adicionar_dia.html', {'form': form})

@login_required
def checkin_dia(request, dia_id):
    dia = get_object_or_404(DiaEvento, pk=dia_id)
    adolescentes = Adolescente.objects.all()
    filtro = request.GET.get('filtro', 'todos')  # padrão: todos
    busca = request.GET.get('busca', '')  # busca por nome

    presencas = Presenca.objects.filter(dia=dia)
    presentes_ids = presencas.filter(presente=True).values_list('adolescente_id', flat=True)

    # Aplica filtro
    if filtro == 'presentes':
        adolescentes = adolescentes.filter(id__in=presentes_ids)
    elif filtro == 'ausentes':
        adolescentes = adolescentes.exclude(id__in=presentes_ids)

    # Aplica busca por nome
    if busca:
        adolescentes = buscar_adolescentes_por_nome(adolescentes, busca)

    # Ordena: primeiro os presentes
    adolescentes = sorted(adolescentes, key=lambda x: x.id not in presentes_ids)

    # Paginação
    paginator = Paginator(adolescentes, 20)  # 20 adolescentes por página
    page = request.GET.get('page')
    try:
        adolescentes_paginados = paginator.page(page)
    except PageNotAnInteger:
        adolescentes_paginados = paginator.page(1)
    except EmptyPage:
        adolescentes_paginados = paginator.page(paginator.num_pages)

    if request.method == 'POST':
        # Se for o modal de contagem de auditório
        if request.POST.get('contagem_auditorio'):
            quantidade = request.POST.get('quantidade_pessoas')
            try:
                quantidade = int(quantidade)
                if quantidade <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                messages.error(request, 'Digite um número válido para a contagem.')
                return redirect('checkin_dia', dia_id=dia.id)
            # Atualiza ou cria a contagem para o dia
            contagem, created = ContagemAuditorio.objects.update_or_create(
                dia=dia,
                defaults={
                    'quantidade_pessoas': quantidade,
                    'usuario_registro': request.user
                }
            )
            if created:
                messages.success(request, f'Contagem registrada: {quantidade} pessoas no auditório!')
            else:
                messages.success(request, f'Contagem atualizada: {quantidade} pessoas no auditório!')
            return redirect('checkin_dia', dia_id=dia.id)
        # Check-in normal
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
        'adolescentes': adolescentes_paginados,
        'presentes_ids': presentes_ids,
        'filtro': filtro,
        'busca': busca,
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
        genero_pg = request.POST.get('lider')

        if nome:
            PequenoGrupo.objects.create(nome=nome, genero_pg=genero_pg)
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


def exportar_adolescentes_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="adolescentes.csv"'

    writer = csv.writer(response)
    writer.writerow(['Nome', 'Sobrenome', 'Data de Nascimento', 'Gênero', 'PG', 'Império'])

    for adolescente in Adolescente.objects.select_related('pg', 'imperio').all():
        writer.writerow([
            adolescente.nome,
            adolescente.sobrenome,
            adolescente.data_nascimento,
            adolescente.get_genero_display(),
            adolescente.pg.nome if adolescente.pg else '',
            adolescente.imperio.nome if adolescente.imperio else ''
        ])

    return response

def exportar_presencas_csv(request):
    dia_id = request.GET.get('dia_id')
    
    if dia_id:
        # Exportar presenças de um dia específico
        try:
            dia = DiaEvento.objects.get(id=dia_id)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="presencas_{dia.data.strftime("%d_%m_%Y")}.csv"'

            writer = csv.writer(response)
            writer.writerow(['Data', 'Nome', 'Presente'])

            presencas = Presenca.objects.filter(dia=dia).select_related('adolescente').order_by('adolescente__nome')

            for presenca in presencas:
                writer.writerow([
                    dia.data.strftime('%d/%m/%Y'),
                    f'{presenca.adolescente.nome} {presenca.adolescente.sobrenome}',
                    'Sim' if presenca.presente else 'Não'
                ])

            return response
        except DiaEvento.DoesNotExist:
            messages.error(request, "Dia não encontrado.")
            return redirect('lista_dias_evento')
    else:
        # Redirecionar para a página de seleção de dia
        return redirect('selecionar_dia_exportar')

def selecionar_dia_exportar(request):
    dias = DiaEvento.objects.annotate(
        total_presentes=Count('presenca', filter=Q(presenca__presente=True))
    ).order_by('-data')
    
    return render(request, 'checkin/selecionar_dia_exportar.html', {
        'dias': dias
    })

@permission_required('adolescentes.view_dashboard', raise_exception=True)
@login_required
def dashboard(request):
    """Dashboard com estatísticas e gráficos"""
    from datetime import timedelta
    
    # Filtros de data
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    dia_especifico = request.GET.get('dia_especifico')
    
    # Estatísticas básicas
    total_adolescentes = Adolescente.objects.count()
    total_pgs = PequenoGrupo.objects.count()
    total_imperios = Imperio.objects.count()
    total_eventos = DiaEvento.objects.count()
    
    # Filtrar eventos por período se especificado
    eventos_query = DiaEvento.objects.all()
    if dia_especifico:
        try:
            dia = DiaEvento.objects.get(data=dia_especifico)
            eventos_query = DiaEvento.objects.filter(data=dia_especifico)
        except DiaEvento.DoesNotExist:
            eventos_query = DiaEvento.objects.none()
    elif data_inicio and data_fim:
        eventos_query = DiaEvento.objects.filter(data__range=[data_inicio, data_fim])
    
    # Presença média por evento no período
    if eventos_query.exists():
        total_presencas = Presenca.objects.filter(
            dia__in=eventos_query, 
            presente=True
        ).count()
        total_eventos = eventos_query.count()
        media_presenca = round(total_presencas / max(total_eventos, 1), 1)
    else:
        media_presenca = 0
    
    # Distribuição por gênero
    generos = Adolescente.objects.values('genero').annotate(
        total=Count('id')
    ).order_by('genero')
    
    genero_labels = []
    genero_data = []
    for genero in generos:
        genero_labels.append(genero['genero'])
        genero_data.append(genero['total'])
    
    # Presença média por PG (top 5)
    if eventos_query.exists():
        presenca_por_pg = PequenoGrupo.objects.annotate(
            total_presentes=Count('adolescentes__presenca', 
                filter=Q(adolescentes__presenca__presente=True, 
                        adolescentes__presenca__dia__in=eventos_query)),
            total_eventos=Count('adolescentes__presenca__dia', 
                filter=Q(adolescentes__presenca__dia__in=eventos_query), 
                distinct=True)
        ).annotate(
            media_presenca=Case(
                When(total_eventos=0, then=Value(0)),
                default=F('total_presentes') / F('total_eventos')
            )
        ).order_by('-media_presenca')[:5]
    else:
        presenca_por_pg = []
    
    pg_labels = []
    pg_data = []
    for pg in presenca_por_pg:
        pg_labels.append(pg.nome)
        pg_data.append(round(pg.media_presenca, 1))
    
    # Evolução da presença (últimos 10 eventos)
    ultimos_eventos = eventos_query.order_by('-data')[:10] if eventos_query.exists() else []
    presenca_por_evento = []
    for evento in reversed(ultimos_eventos):  # Inverter para ordem cronológica
        presentes = Presenca.objects.filter(dia=evento, presente=True).count()
        total = Presenca.objects.filter(dia=evento).count()
        # Calcular percentual em relação ao total de adolescentes cadastrados
        percentual = round((presentes / max(total_adolescentes, 1)) * 100, 1)
        presenca_por_evento.append({
            'data': evento.data.strftime('%d/%m'),
            'presentes': presentes,
            'total': total,
            'percentual': percentual
        })
    
    # Presença média por Império
    if eventos_query.exists():
        presenca_por_imperio = Imperio.objects.annotate(
            total_presentes=Count('adolescente__presenca', 
                filter=Q(adolescente__presenca__presente=True, 
                        adolescente__presenca__dia__in=eventos_query)),
            total_eventos=Count('adolescente__presenca__dia', 
                filter=Q(adolescente__presenca__dia__in=eventos_query), 
                distinct=True)
        ).annotate(
            media_presenca=Case(
                When(total_eventos=0, then=Value(0)),
                default=F('total_presentes') / F('total_eventos')
            )
        ).order_by('-media_presenca')
    else:
        presenca_por_imperio = []
    
    imperio_labels = []
    imperio_data = []
    for imperio in presenca_por_imperio:
        imperio_labels.append(imperio.nome)
        imperio_data.append(round(imperio.media_presenca, 1))
    
    # Estatísticas do último evento
    ultimo_evento = eventos_query.order_by('-data').first() if eventos_query.exists() else None
    if ultimo_evento:
        ultimo_presentes = Presenca.objects.filter(dia=ultimo_evento, presente=True).count()
        ultimo_total = Presenca.objects.filter(dia=ultimo_evento).count()
        # Calcular percentual em relação ao total de adolescentes cadastrados
        ultimo_percentual = round((ultimo_presentes / max(total_adolescentes, 1)) * 100, 1)
    else:
        ultimo_presentes = 0
        ultimo_total = 0
        ultimo_percentual = 0
    
    # Lista de eventos para o filtro
    todos_eventos = DiaEvento.objects.order_by('-data')
    
    evolucao_labels = [e['data'] for e in presenca_por_evento]
    evolucao_data = [e['presentes'] for e in presenca_por_evento]
    evolucao_total = [e['total'] for e in presenca_por_evento]
    
    # Contagem de auditório por evento
    contagem_auditorio_total = 0
    contagem_auditorio_media = 0
    contagem_auditorio_ultimo = None
    contagem_auditorio_ultimo_usuario = None
    contagem_auditorio_ultimo_data = None
    if eventos_query.exists():
        contagens = ContagemAuditorio.objects.filter(dia__in=eventos_query)
        contagem_auditorio_media = round(contagem_auditorio_total / max(contagens.count(), 1), 1)
        # Última contagem
        ultima_contagem = contagens.order_by('-dia__data').first()
        if ultima_contagem:
            contagem_auditorio_ultimo = ultima_contagem.quantidade_pessoas
            contagem_auditorio_ultimo_usuario = ultima_contagem.usuario_registro.username
            contagem_auditorio_ultimo_data = ultima_contagem.dia.data

    context = {
        'total_adolescentes': total_adolescentes,
        'total_pgs': total_pgs,
        'total_imperios': total_imperios,
        'total_eventos': total_eventos,
        'media_presenca': media_presenca,
        'ultimo_presentes': ultimo_presentes,
        'ultimo_total': ultimo_total,
        'ultimo_percentual': ultimo_percentual,
        'ultimo_evento': ultimo_evento,
        
        # Filtros
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'dia_especifico': dia_especifico,
        'todos_eventos': todos_eventos,
        
        # Dados para gráficos
        'genero_labels': genero_labels,
        'genero_data': genero_data,
        'pg_labels': pg_labels,
        'pg_data': pg_data,
        'presenca_por_evento': presenca_por_evento,
        'evolucao_labels': evolucao_labels,
        'evolucao_data': evolucao_data,
        'evolucao_total': evolucao_total,
        'imperio_labels': imperio_labels,
        'imperio_data': imperio_data,
        'contagem_auditorio_total': contagem_auditorio_total,
        'contagem_auditorio_media': contagem_auditorio_media,
        'contagem_auditorio_ultimo': contagem_auditorio_ultimo,
        'contagem_auditorio_ultimo_usuario': contagem_auditorio_ultimo_usuario,
        'contagem_auditorio_ultimo_data': contagem_auditorio_ultimo_data,
    }
    
    return render(request, 'adolescentes/dashboard.html', context)

@login_required
def contagem_auditorio(request):
    """Gerencia contagens de auditório - adicionar, editar ou visualizar"""
    if request.method == 'POST':
        form = ContagemAuditorioForm(request.POST)
        if form.is_valid():
            dia_evento = form.cleaned_data['dia']
            quantidade = form.cleaned_data['quantidade_pessoas']
            
            # Verificar se já existe uma contagem para este dia
            contagem_existente = ContagemAuditorio.objects.filter(dia=dia_evento).first()
            
            if contagem_existente:
                # Atualizar contagem existente
                contagem_existente.quantidade_pessoas = quantidade
                contagem_existente.usuario_registro = request.user
                contagem_existente.save()
                messages.success(request, f'Contagem atualizada! {quantidade} pessoas para o evento de {dia_evento.data.strftime("%d/%m/%Y")}.')
            else:
                # Criar nova contagem
                ContagemAuditorio.objects.create(
                    dia=dia_evento,
                    quantidade_pessoas=quantidade,
                    usuario_registro=request.user
                )
                messages.success(request, f'Contagem registrada! {quantidade} pessoas para o evento de {dia_evento.data.strftime("%d/%m/%Y")}.')
            
            return redirect('contagem_auditorio')
    else:
        form = ContagemAuditorioForm()
    
    # Buscar contagens existentes
    contagens = ContagemAuditorio.objects.select_related('dia', 'usuario_registro').all().order_by('-dia__data')
    
    context = {
        'form': form,
        'contagens': contagens,
        'titulo_pagina': 'Contagem de Auditório'
    }
    return render(request, 'checkin/contagem_auditorio.html', context)