from datetime import date, datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from .models import Adolescente, DiaEvento, Presenca, PequenoGrupo, Imperio, ContagemAuditorio, ContagemVisitantes, DuplicadoRejeitado
from .forms import AdolescenteForm, DiaEventoForm, ContagemAuditorioForm, ContagemVisitantesForm
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
from django.db import transaction, connection
from django.template.loader import render_to_string

# Constantes para anos disponíveis
ANO_ATUAL = 2026
ANOS_DISPONIVEIS = [2025, 2026]

def get_ano_selecionado(request):
    """Retorna o ano selecionado na sessão do usuário (padrão: 2026)"""
    return request.session.get('ano_selecionado', ANO_ATUAL)

def is_ano_readonly(request):
    """Verifica se o ano selecionado é readonly (anos anteriores ao atual)"""
    ano = get_ano_selecionado(request)
    return ano < ANO_ATUAL

try:
    # Disponível quando usando PostgreSQL e habilitando django.contrib.postgres
    from django.contrib.postgres.search import TrigramSimilarity
except Exception:  # pragma: no cover
    TrigramSimilarity = None

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

def pagina_inicial(request):
    """
    Página inicial que redireciona adequadamente sem causar loops.
    Se usuário está logado, vai para lista de adolescentes.
    Se não está logado, vai para login.
    """
    if request.user.is_authenticated:
        return redirect('listar_adolescentes')
    else:
        return redirect('login')

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
def trocar_ano(request, ano):
    """Troca o ano selecionado na sessão do usuário"""
    if ano in ANOS_DISPONIVEIS:
        request.session['ano_selecionado'] = ano
        messages.success(request, f"Visualizando dados de {ano}")
    else:
        messages.error(request, f"Ano {ano} não disponível")
    
    # Redireciona para a página anterior ou para a lista de adolescentes
    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', reverse('listar_adolescentes')))
    return redirect(next_url)

@login_required
def listar_adolescentes(request):
    busca = request.GET.get('busca', '')
    pg_id = request.GET.get('pg')
    genero = request.GET.get('genero')
    imperio_id = request.GET.get('imperio')
    presenca_filtro = request.GET.get('presenca')
    ano_nascimento = request.GET.get('ano_nascimento')
    
    # Parâmetros de ordenação
    ordenar_por = request.GET.get('ordenar_por', 'nome')  # Padrão: ordenar por nome
    direcao = request.GET.get('direcao', 'asc')  # Padrão: ascendente

    # Filtrar por ano selecionado
    ano = get_ano_selecionado(request)
    readonly = is_ano_readonly(request)
    
    # Otimização: usar select_related e prefetch_related para evitar queries N+1
    adolescentes = Adolescente.objects.filter(ano=ano).select_related('pg', 'imperio').prefetch_related(
        Prefetch('presenca_set', 
                queryset=Presenca.objects.select_related('dia').order_by('-dia__data')[:5],
                to_attr='cached_ultimas_presencas')
    )
    if busca:
        adolescentes = buscar_adolescentes_por_nome(adolescentes, busca)
    if pg_id:
        if pg_id == 'sem_pg':
            adolescentes = adolescentes.filter(pg__isnull=True)
        else:
            adolescentes = adolescentes.filter(pg__id=pg_id)
    if genero:
        adolescentes = adolescentes.filter(genero=genero)
    if imperio_id:
        if imperio_id == 'sem_imperio':
            adolescentes = adolescentes.filter(imperio__isnull=True)
        else:
            adolescentes = adolescentes.filter(imperio__id=imperio_id)

    # Filtro por ano de nascimento
    if ano_nascimento:
        try:
            ano_nasc_int = int(ano_nascimento)
            adolescentes = adolescentes.filter(data_nascimento__year=ano_nasc_int)
        except ValueError:
            pass

    # Filtro por presença
    if presenca_filtro:
        trinta_dias_atras = date.today() - timedelta(days=30)
        if presenca_filtro == 'presente_30':
            adolescentes = adolescentes.filter(
                presenca__presente=True,
                presenca__dia__data__gte=trinta_dias_atras,
            ).distinct()
        elif presenca_filtro == 'ausente_30':
            # Não teve nenhuma presença (presente=True) nos últimos 30 dias
            adolescentes = adolescentes.exclude(
                presenca__presente=True,
                presenca__dia__data__gte=trinta_dias_atras,
            ).distinct()
        elif presenca_filtro == 'nunca':
            # Nunca compareceu (sem nenhum registro de presença)
            adolescentes = adolescentes.filter(presenca__isnull=True).distinct()

    # Aplicar ordenação
    if ordenar_por == 'nome':
        if direcao == 'asc':
            adolescentes = adolescentes.order_by('nome', 'sobrenome')
        else:
            adolescentes = adolescentes.order_by('-nome', '-sobrenome')
    elif ordenar_por == 'sobrenome':
        if direcao == 'asc':
            adolescentes = adolescentes.order_by('sobrenome', 'nome')
        else:
            adolescentes = adolescentes.order_by('-sobrenome', '-nome')
    elif ordenar_por == 'genero':
        if direcao == 'asc':
            adolescentes = adolescentes.order_by('genero', 'nome', 'sobrenome')
        else:
            adolescentes = adolescentes.order_by('-genero', '-nome', '-sobrenome')
    elif ordenar_por == 'data_nascimento':
        if direcao == 'asc':
            adolescentes = adolescentes.order_by('data_nascimento', 'nome', 'sobrenome')
        else:
            adolescentes = adolescentes.order_by('-data_nascimento', '-nome', '-sobrenome')
    elif ordenar_por == 'pg':
        if direcao == 'asc':
            adolescentes = adolescentes.order_by('pg__nome', 'nome', 'sobrenome')
        else:
            adolescentes = adolescentes.order_by('-pg__nome', '-nome', '-sobrenome')
    elif ordenar_por == 'imperio':
        if direcao == 'asc':
            adolescentes = adolescentes.order_by('imperio__nome', 'nome', 'sobrenome')
        else:
            adolescentes = adolescentes.order_by('-imperio__nome', '-nome', '-sobrenome')
    else:
        # Padrão: ordenar por nome e sobrenome
        adolescentes = adolescentes.order_by('nome', 'sobrenome')

    total_adolescentes = adolescentes.count()
    
    # Otimização: cache para filtros (evita queries repetidas) - filtrar por ano
    pgs = PequenoGrupo.objects.filter(ano=ano)
    imperios = Imperio.objects.filter(ano=ano)
    
    # Anos de nascimento disponíveis para o filtro
    anos_nascimento = sorted(
        Adolescente.objects.filter(ano=ano)
        .exclude(data_nascimento__isnull=True)
        .values_list('data_nascimento__year', flat=True)
        .distinct()
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

    # DESABILITADO: Formulários inline causam 54 queries N+1 
    # A funcionalidade de edição inline será reimplementada de forma otimizada
    # Por enquanto, usar apenas os links de edição individuais
    pass

    return render(request, 'adolescentes/listar.html', {
        'adolescentes': adolescentes_paginados,
        'total_adolescentes': total_adolescentes,
        'pgs': pgs,
        'imperios': imperios,
        'busca': busca,
        'pg_selecionado': pg_id,
        'genero_selecionado': genero,
        'imperio_selecionado': imperio_id,
        'presenca_selecionada': presenca_filtro,
        'ano_nascimento_selecionado': ano_nascimento,
        'anos_nascimento': anos_nascimento,
        'ordenar_por': ordenar_por,
        'direcao': direcao,
        'ano_selecionado': ano,
        'anos_disponiveis': ANOS_DISPONIVEIS,
        'readonly': readonly,
    })


@login_required
@permission_required('adolescentes.review_duplicates', raise_exception=True)
@require_http_methods(["GET"])
def sugestoes_duplicados(request):
    """
    Retorna pares candidatos a duplicados com mesma data_nascimento e alta similaridade de nome completo.
    Usa função similarity do pg_trgm via SQL bruto para desempenho.
    """
    threshold = float(request.GET.get('threshold', '0.75'))
    limit = int(request.GET.get('limit', '50'))

    # Estratégias combinadas:
    # 1) Mesma data de nascimento + similaridade >= threshold (pg_trgm)
    # 2) Nome e sobrenome exatamente iguais e data de nascimento diferente (incluir mesmo se similarity < threshold)
    #    - Para (2), o score é reduzido (ex.: 0.70) e marcamos datas_diferentes=true para a UI exibir aviso.
    sql = """
        (
          SELECT a.id AS id_a, b.id AS id_b,
                 a.nome || ' ' || a.sobrenome AS nome_a,
                 b.nome || ' ' || b.sobrenome AS nome_b,
                 a.data_nascimento AS data_nasc_a,
                 b.data_nascimento AS data_nasc_b,
                 similarity(a.nome || ' ' || a.sobrenome, b.nome || ' ' || b.sobrenome) AS score,
                 FALSE AS datas_diferentes,
                 (a.pg_id IS NOT NULL) AS a_has_pg,
                 (a.imperio_id IS NOT NULL) AS a_has_imp,
                 (b.pg_id IS NOT NULL) AS b_has_pg,
                 (b.imperio_id IS NOT NULL) AS b_has_imp,
                 CASE
                   WHEN a.pg_id IS NOT NULL AND b.pg_id IS NULL THEN a.id
                   WHEN b.pg_id IS NOT NULL AND a.pg_id IS NULL THEN b.id
                   WHEN a.imperio_id IS NOT NULL AND b.imperio_id IS NULL THEN a.id
                   WHEN b.imperio_id IS NOT NULL AND a.imperio_id IS NULL THEN b.id
                   ELSE NULL
                 END AS recommended_winner
          FROM adolescentes_adolescente a
          JOIN adolescentes_adolescente b
            ON a.id < b.id
           AND a.data_nascimento = b.data_nascimento
          LEFT JOIN adolescentes_duplicadorejeitado r
            ON r.adolescente_a_id = a.id AND r.adolescente_b_id = b.id
          WHERE similarity(a.nome || ' ' || a.sobrenome, b.nome || ' ' || b.sobrenome) >= %s
            AND r.id IS NULL
        )
        UNION ALL
        (
          SELECT a.id AS id_a, b.id AS id_b,
                 a.nome || ' ' || a.sobrenome AS nome_a,
                 b.nome || ' ' || b.sobrenome AS nome_b,
                 a.data_nascimento AS data_nasc_a,
                 b.data_nascimento AS data_nasc_b,
                 0.70 AS score,
                 TRUE AS datas_diferentes,
                 (a.pg_id IS NOT NULL) AS a_has_pg,
                 (a.imperio_id IS NOT NULL) AS a_has_imp,
                 (b.pg_id IS NOT NULL) AS b_has_pg,
                 (b.imperio_id IS NOT NULL) AS b_has_imp,
                 CASE
                   WHEN a.pg_id IS NOT NULL AND b.pg_id IS NULL THEN a.id
                   WHEN b.pg_id IS NOT NULL AND a.pg_id IS NULL THEN b.id
                   WHEN a.imperio_id IS NOT NULL AND b.imperio_id IS NULL THEN a.id
                   WHEN b.imperio_id IS NOT NULL AND a.imperio_id IS NULL THEN b.id
                   ELSE NULL
                 END AS recommended_winner
          FROM adolescentes_adolescente a
          JOIN adolescentes_adolescente b
            ON a.id < b.id
           AND a.nome = b.nome
           AND a.sobrenome = b.sobrenome
           AND a.data_nascimento IS DISTINCT FROM b.data_nascimento
          LEFT JOIN adolescentes_duplicadorejeitado r
            ON r.adolescente_a_id = a.id AND r.adolescente_b_id = b.id
          WHERE r.id IS NULL
        )
        ORDER BY score DESC
        LIMIT %s
    """
    try:
        with connection.cursor() as cur:
            cur.execute(sql, [threshold, limit])
            rows = cur.fetchall()
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': str(e),
            'hint': 'Certifique-se de que a extensão pg_trgm está habilitada.'
        }, status=500)

    results = []
    for r in rows:
        (
            id_a, id_b, nome_a, nome_b,
            dna, dnb, score, datas_dif,
            a_has_pg, a_has_imp, b_has_pg, b_has_imp,
            recommended_winner
        ) = r
        results.append({
            'id_a': id_a,
            'id_b': id_b,
            'nome_a': nome_a,
            'nome_b': nome_b,
            'data_nascimento_a': dna.strftime('%Y-%m-%d') if dna else None,
            'data_nascimento_b': dnb.strftime('%Y-%m-%d') if dnb else None,
            'score': float(score),
            'datas_diferentes': bool(datas_dif),
            'a_has_pg': bool(a_has_pg),
            'a_has_imp': bool(a_has_imp),
            'b_has_pg': bool(b_has_pg),
            'b_has_imp': bool(b_has_imp),
            'recommended_winner': int(recommended_winner) if recommended_winner is not None else None,
        })
    return JsonResponse({'ok': True, 'results': results})


@login_required
@permission_required('adolescentes.review_duplicates', raise_exception=True)
@require_http_methods(["POST"])
def merge_duplicados(request):
    """
    Mescla dois perfis: winner_id mantém, loser_id é fundido e removido.
    - Reatribui Presenças para o vencedor (evita duplicar por mesmo dia).
    - Copia foto se vencedor não tiver.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST
    winner_id = int(payload.get('winner_id'))
    loser_id = int(payload.get('loser_id'))
    dry_run = str(payload.get('dry_run', 'false')).lower() == 'true'
    allow_diff_dob = str(payload.get('allow_diff_dob', 'false')).lower() == 'true'

    if winner_id == loser_id:
        return JsonResponse({'ok': False, 'error': 'IDs iguais'}, status=400)

    winner = get_object_or_404(Adolescente, id=winner_id)
    loser = get_object_or_404(Adolescente, id=loser_id)

    # Proteção básica: bloquear datas diferentes salvo confirmação explícita
    if winner.data_nascimento != loser.data_nascimento and not allow_diff_dob:
        return JsonResponse({'ok': False, 'error': 'Datas de nascimento diferentes. Confirme para prosseguir.'}, status=400)

    changes = {'presencas_movidas': 0, 'foto_copiada': False}

    if dry_run:
        return JsonResponse({'ok': True, 'dry_run': True, 'changes': changes})

    with transaction.atomic():
        # Reatribuir presenças do perdedor para o vencedor, evitando duplicar por mesmo dia
        loser_presencas = Presenca.objects.filter(adolescente=loser)
        for p in loser_presencas.select_related('dia'):
            exists = Presenca.objects.filter(adolescente=winner, dia=p.dia, presente=p.presente).exists()
            if not exists:
                p.adolescente = winner
                p.save(update_fields=['adolescente'])
                changes['presencas_movidas'] += 1
            else:
                p.delete()

        # Foto: se winner não tem e loser tem, copiar
        if not winner.foto and loser.foto:
            winner.foto = loser.foto
            winner.save(update_fields=['foto'])
            changes['foto_copiada'] = True

        # Finalmente apagar perdedor
        loser.delete()

    return JsonResponse({'ok': True, 'changes': changes})


@login_required
@permission_required('adolescentes.review_duplicates', raise_exception=True)
@require_http_methods(["POST"])
def rejeitar_duplicado(request):
    """Persiste a rejeição de um par para não sugerir novamente."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST
    try:
        id_a = int(payload.get('id_a'))
        id_b = int(payload.get('id_b'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Par inválido'}, status=400)

    if id_a == id_b:
        return JsonResponse({'ok': False, 'error': 'IDs iguais'}, status=400)

    # garantir ordem
    a_id, b_id = (id_a, id_b) if id_a < id_b else (id_b, id_a)
    a = get_object_or_404(Adolescente, id=a_id)
    b = get_object_or_404(Adolescente, id=b_id)
    motivo = payload.get('motivo') or ''
    obj, created = DuplicadoRejeitado.objects.get_or_create(
        adolescente_a=a, adolescente_b=b,
        defaults={'criado_por': request.user, 'motivo': motivo}
    )
    if not created:
        # atualizar quem rejeitou/motivo mais recente
        obj.criado_por = request.user
        if motivo:
            obj.motivo = motivo
        obj.save(update_fields=['criado_por', 'motivo'])
    return JsonResponse({'ok': True, 'rejeitado': True})

@login_required
def pagina_checkin(request):
    return render(request, 'checkin.html')

@login_required
def pagina_pgs(request):
    return render(request, 'pgs.html')

@login_required
def criar_adolescente(request):
    ano = get_ano_selecionado(request)
    if is_ano_readonly(request):
        messages.error(request, "Não é possível criar adolescentes em anos anteriores.")
        return redirect('listar_adolescentes')
    
    # Detecta se está vindo da página de check-in
    next_url = request.GET.get('next', '')
    dia_id = None
    
    # Extrai o dia_id da URL de check-in (formato: /checkin/123/)
    if '/checkin/' in next_url and next_url.count('/') >= 3:
        try:
            parts = next_url.strip('/').split('/')
            if len(parts) >= 2 and parts[0] == 'checkin':
                dia_id = int(parts[1])
                # Verifica se o dia existe
                DiaEvento.objects.get(id=dia_id)
        except (ValueError, DiaEvento.DoesNotExist):
            dia_id = None
    
    if request.method == "POST":
        form = AdolescenteForm(request.POST, request.FILES, ano=ano)
        if form.is_valid():
            # Verifica se a data de nascimento não é futura
            data_nascimento = form.cleaned_data['data_nascimento']
            if data_nascimento > datetime.now().date():
                messages.error(request, "A data de nascimento não pode ser no futuro.")
                return redirect('criar_adolescente')

            adolescente = form.save(commit=False)
            adolescente.ano = ano
            adolescente.save()
            
            # Se veio da página de check-in, cria automaticamente o check-in para aquele dia
            if dia_id:
                try:
                    dia = DiaEvento.objects.get(id=dia_id)
                    Presenca.objects.update_or_create(
                        adolescente=adolescente,
                        dia=dia,
                        defaults={'presente': True}
                    )
                    messages.success(request, f"Adolescente {adolescente.nome} criado e check-in confirmado para {dia.data.strftime('%d/%m/%Y')}!")
                    return redirect('checkin_dia', dia_id=dia_id)
                except DiaEvento.DoesNotExist:
                    messages.warning(request, "Adolescente criado, mas não foi possível fazer o check-in automático.")
            else:
                # Check-in automático: se existe evento hoje, marcar presença
                hoje = date.today()
                evento_hoje = DiaEvento.objects.filter(data=hoje, ano=ano).first()
                if evento_hoje:
                    Presenca.objects.update_or_create(
                        adolescente=adolescente,
                        dia=evento_hoje,
                        defaults={'presente': True}
                    )
                    messages.success(request, f"Adolescente criado e check-in automático para {evento_hoje}!")
                else:
                    messages.success(request, "Adolescente criado com sucesso!")
            
            # Redireciona para a página de origem ou lista padrão
            if next_url:
                return redirect(next_url)
            return redirect('listar_adolescentes')
    else:
        form = AdolescenteForm(ano=ano)
    
    # Verificar se existe evento hoje para mostrar aviso no template
    hoje = date.today()
    evento_hoje = DiaEvento.objects.filter(data=hoje, ano=ano).first()
    
    context = {'form': form, 'evento_hoje': evento_hoje}
    if dia_id:
        try:
            dia = DiaEvento.objects.get(id=dia_id)
            context['dia_checkin'] = dia
        except DiaEvento.DoesNotExist:
            pass
    
    return render(request, 'adolescentes/criar_adolescente.html', context)

@permission_required('adolescentes.change_adolescente', raise_exception=True)
@login_required
def get_form_ajax(request, adolescente_id):
    """Endpoint AJAX para carregar formulário de edição sob demanda"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        adolescente = get_object_or_404(Adolescente, id=adolescente_id)
        form = AdolescenteForm(instance=adolescente)
        
        # Renderizar apenas o conteúdo do formulário
        form_html = render_to_string('adolescentes/partials/form_edicao.html', {
            'form': form,
            'adolescente': adolescente,
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'form_html': form_html,
            'adolescente_id': adolescente_id,
            'adolescente_nome': f"{adolescente.nome} {adolescente.sobrenome}"
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def editar_adolescente(request, id):
    adolescente = get_object_or_404(Adolescente, id=id)
    
    if request.method == 'POST':
        form = AdolescenteForm(request.POST, request.FILES, instance=adolescente)
        if form.is_valid():
            # Verificar se deve remover a foto atual
            if request.POST.get('foto-clear'):
                adolescente.foto.delete(save=False)  # Remove o arquivo
                adolescente.foto = None  # Remove a referência
            
            form.save()
            messages.success(request, "Adolescente atualizado com sucesso.")
            
            # Redireciona mantendo filtros, busca e página
            params = request.GET.urlencode() or request.POST.get('params', '')
            url = reverse('listar_adolescentes')
            if params:
                url = f"{url}?{params}"
            return redirect(url)
        else:
            messages.error(request, "Não foi possível salvar. Verifique os campos e tente novamente.")
    else:
        form = AdolescenteForm(instance=adolescente)
    
    return render(request, 'adolescentes/criar_adolescente.html', {
        'form': form,
        'adolescente': adolescente,
        'titulo': f'Editar {adolescente.nome} {adolescente.sobrenome}'
    })

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
    ano = get_ano_selecionado(request)
    readonly = is_ano_readonly(request)
    
    dias_list = DiaEvento.objects.filter(ano=ano).prefetch_related('contagens_auditorio').order_by('-data')
    
    # Calcular média usando contagem de auditório (prioritário) ou check-in (fallback)
    total_contagens = 0
    soma_pessoas = 0
    
    for dia in dias_list:
        # Anotar total de presentes via check-in para cada dia
        dia.total_presentes_checkin = Presenca.objects.filter(dia=dia, presente=True).count()
        
        # Buscar contagem de auditório
        contagem_auditorio = dia.contagens_auditorio.first()
        if contagem_auditorio:
            dia.total_presentes = contagem_auditorio.quantidade_pessoas
            dia.fonte = 'auditorio'
            soma_pessoas += contagem_auditorio.quantidade_pessoas
            total_contagens += 1
        else:
            dia.total_presentes = dia.total_presentes_checkin
            dia.fonte = 'checkin'
    
    # Média baseada apenas em contagens de auditório
    if total_contagens > 0:
        media_presentes = soma_pessoas / total_contagens
    else:
        media_presentes = 0
    
    # Paginação - 20 dias por página
    paginator = Paginator(dias_list, 20)
    page = request.GET.get('page')
    try:
        dias = paginator.page(page)
    except PageNotAnInteger:
        dias = paginator.page(1)
    except EmptyPage:
        dias = paginator.page(paginator.num_pages)

    return render(request, 'checkin/lista_dias.html', {
        'dias': dias,
        'media_presentes': media_presentes,
        'pode_adicionar_dia': request.user.has_perm('adolescentes.add_diaevento') and not readonly,
        'ano_selecionado': ano,
        'anos_disponiveis': ANOS_DISPONIVEIS,
        'readonly': readonly,
    })


@login_required
@permission_required('adolescentes.add_diaevento', raise_exception=True)
def adicionar_dia_evento(request):
    ano = get_ano_selecionado(request)
    if is_ano_readonly(request):
        messages.error(request, "Não é possível adicionar eventos em anos anteriores.")
        return redirect('pagina_checkin')
    
    if request.method == 'POST':
        form = DiaEventoForm(request.POST)
        if form.is_valid():
            if DiaEvento.objects.filter(data=form.cleaned_data['data'], ano=ano).exists():
                messages.warning(request, "Esse dia já foi adicionado.")
            else:
                dia_evento = form.save(commit=False)
                dia_evento.ano = ano
                dia_evento.save()
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
    ano = dia.ano  # Usar o ano do evento
    readonly = ano < ANO_ATUAL
    
    adolescentes = Adolescente.objects.filter(ano=ano)
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

    # Ordenação:
    # 1) pela quantidade total de presenças (desc)
    # 2) desempate por ordem alfabética (nome, sobrenome)
    adolescentes = (
        adolescentes
        .annotate(total_presencas=Count('presenca', filter=Q(presenca__presente=True)))
        .order_by('-total_presencas', 'nome', 'sobrenome')
    )

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
            # Verifica permissão de adicionar contagem de auditório
            if not request.user.has_perm('adolescentes.add_contagemauditorio'):
                messages.error(request, 'Você não tem permissão para registrar contagem de auditório.')
                return redirect('checkin_dia', dia_id=dia.id)
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
        
        # Se for o modal de contagem de visitantes
        if request.POST.get('contagem_visitantes'):
            # Verifica permissão de adicionar contagem de visitantes
            if not request.user.has_perm('adolescentes.add_contagemvisitantes'):
                messages.error(request, 'Você não tem permissão para registrar visitantes.')
                return redirect('checkin_dia', dia_id=dia.id)
            quantidade_v = request.POST.get('quantidade_visitantes')
            try:
                quantidade_v = int(quantidade_v)
                if quantidade_v < 0:
                    raise ValueError
            except (TypeError, ValueError):
                messages.error(request, 'Digite um número válido para visitantes (zero ou mais).')
                return redirect('checkin_dia', dia_id=dia.id)
            contagem_v, created_v = ContagemVisitantes.objects.update_or_create(
                dia=dia,
                defaults={
                    'quantidade_visitantes': quantidade_v,
                    'usuario_registro': request.user
                }
            )
            if created_v:
                messages.success(request, f'Visitantes registrados: {quantidade_v}.')
            else:
                messages.success(request, f'Visitantes atualizados: {quantidade_v}.')
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

    # Calcular PG VIP: presentes do dia, sem PG definido, com 3 ou menos presenças totais
    pg_vip_candidatos = []
    presentes_hoje = Adolescente.objects.filter(
        id__in=presentes_ids,
        pg__isnull=True  # Sem PG definido
    ).annotate(
        total_presencas=Count('presenca', filter=Q(presenca__presente=True))
    ).filter(
        total_presencas__lte=3  # 3 ou menos presenças
    ).order_by('total_presencas', 'nome', 'sobrenome')
    
    for adolescente in presentes_hoje:
        pg_vip_candidatos.append({
            'adolescente': adolescente,
            'total_presencas': adolescente.total_presencas,
            'primeira_vez': adolescente.total_presencas == 1
        })

    return render(request, 'checkin/checkin_dia.html', {
        'dia': dia,
        'adolescentes': adolescentes_paginados,
        'presentes_ids': presentes_ids,
        'filtro': filtro,
        'busca': busca,
        'pg_vip_candidatos': pg_vip_candidatos,
        'readonly': readonly,
        'ano_selecionado': ano,
    })

@login_required
def pg_vip(request, dia_id):
    """Página dedicada ao PG VIP de um dia específico"""
    dia = get_object_or_404(DiaEvento, pk=dia_id)
    
    # Buscar presentes do dia
    presencas = Presenca.objects.filter(dia=dia, presente=True)
    presentes_ids = presencas.values_list('adolescente_id', flat=True)
    
    # Buscar todos presentes sem PG definido
    presentes_sem_pg = Adolescente.objects.filter(
        id__in=presentes_ids,
        pg__isnull=True  # Sem PG definido
    ).annotate(
        total_presencas=Count('presenca', filter=Q(presenca__presente=True))
    ).order_by('total_presencas', 'nome', 'sobrenome')
    
    # Separar em duas listas: PG VIP (1-3 vezes) e Precisa Alocar (4+ vezes)
    pg_vip_candidatos = []
    precisa_alocar = []
    
    for adolescente in presentes_sem_pg:
        item = {
            'adolescente': adolescente,
            'total_presencas': adolescente.total_presencas,
            'primeira_vez': adolescente.total_presencas == 1
        }
        
        if adolescente.total_presencas <= 3:
            pg_vip_candidatos.append(item)
        else:
            precisa_alocar.append(item)
    
    return render(request, 'checkin/pg_vip.html', {
        'dia': dia,
        'pg_vip_candidatos': pg_vip_candidatos,
        'precisa_alocar': precisa_alocar,
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
    ano = get_ano_selecionado(request)
    if is_ano_readonly(request):
        messages.error(request, "Não é possível adicionar PGs em anos anteriores.")
        return redirect('lista_pgs')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        genero_pg = request.POST.get('lider')

        if nome:
            PequenoGrupo.objects.create(nome=nome, genero_pg=genero_pg, ano=ano)
            messages.success(request, "PG criado com sucesso.")
            return redirect('lista_pgs')
        else:
            messages.error(request, "O nome do PG é obrigatório.")

    return render(request, 'pgs/adicionar_pg.html')

@permission_required('adolescentes.view_pgs_page', raise_exception=True)
@login_required
def lista_pgs(request):
    ano = get_ano_selecionado(request)
    readonly = is_ano_readonly(request)
    pgs = PequenoGrupo.objects.filter(ano=ano).annotate(total=Count('adolescentes'))
    return render(request, 'pgs/lista_pgs.html', {
        'pgs': pgs,
        'ano_selecionado': ano,
        'anos_disponiveis': ANOS_DISPONIVEIS,
        'readonly': readonly,
    })

@permission_required('adolescentes.view_pgs_page', raise_exception=True)
@login_required
def detalhes_pg(request, pg_id):
    ano = get_ano_selecionado(request)
    readonly = is_ano_readonly(request)
    pg = get_object_or_404(PequenoGrupo, id=pg_id)
    membros = Adolescente.objects.filter(pg=pg, ano=ano).order_by('nome', 'sobrenome')
    disponiveis = Adolescente.objects.filter(ano=ano).exclude(pg=pg).select_related('pg').order_by('nome', 'sobrenome')
    anos_nascimento_disponiveis = sorted(
        disponiveis.exclude(data_nascimento__isnull=True)
        .values_list('data_nascimento__year', flat=True).distinct()
    )
    return render(request, 'pgs/pg.html', {
        'pg': pg,
        'adolescentes': membros,
        'disponiveis': disponiveis,
        'anos_nascimento_disponiveis': anos_nascimento_disponiveis,
        'readonly': readonly,
        'ano_selecionado': ano,
    })


@login_required
@require_http_methods(["POST"])
def bulk_add_pg(request, pg_id):
    """Adicionar múltiplos adolescentes a um PG via AJAX"""
    if is_ano_readonly(request):
        return JsonResponse({'ok': False, 'error': 'Ano somente leitura'}, status=403)
    pg = get_object_or_404(PequenoGrupo, id=pg_id)
    data = json.loads(request.body)
    ids = data.get('ids', [])
    count = Adolescente.objects.filter(id__in=ids, ano=pg.ano).update(pg=pg)
    return JsonResponse({'ok': True, 'count': count})


@login_required
@require_http_methods(["POST"])
def bulk_remove_pg(request, pg_id):
    """Remover múltiplos adolescentes de um PG via AJAX"""
    if is_ano_readonly(request):
        return JsonResponse({'ok': False, 'error': 'Ano somente leitura'}, status=403)
    pg = get_object_or_404(PequenoGrupo, id=pg_id)
    data = json.loads(request.body)
    ids = data.get('ids', [])
    count = Adolescente.objects.filter(id__in=ids, pg=pg).update(pg=None)
    return JsonResponse({'ok': True, 'count': count})


@permission_required('adolescentes.view_pgs_page', raise_exception=True)
@login_required
def lista_imperios(request):
    ano = get_ano_selecionado(request)
    readonly = is_ano_readonly(request)
    imperios = Imperio.objects.filter(ano=ano).annotate(total=Count('adolescente'))
    return render(request, 'imperios/lista_imperios.html', {
        'imperios': imperios,
        'ano_selecionado': ano,
        'anos_disponiveis': ANOS_DISPONIVEIS,
        'readonly': readonly,
    })


@login_required
def adicionar_imperio(request):
    ano = get_ano_selecionado(request)
    if is_ano_readonly(request):
        messages.error(request, "Não é possível adicionar Impérios em anos anteriores.")
        return redirect('lista_imperios')
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            Imperio.objects.create(nome=nome, ano=ano)
            messages.success(request, "Império criado com sucesso.")
            return redirect('lista_imperios')
        else:
            messages.error(request, "O nome do Império é obrigatório.")
    return render(request, 'imperios/adicionar_imperio.html')


@permission_required('adolescentes.view_pgs_page', raise_exception=True)
@login_required
def detalhes_imperio(request, imperio_id):
    ano = get_ano_selecionado(request)
    readonly = is_ano_readonly(request)
    imperio = get_object_or_404(Imperio, id=imperio_id)
    membros = Adolescente.objects.filter(imperio=imperio, ano=ano).order_by('nome', 'sobrenome')
    disponiveis = Adolescente.objects.filter(ano=ano).exclude(imperio=imperio).select_related('imperio', 'pg').order_by('nome', 'sobrenome')
    anos_nascimento_disponiveis = sorted(
        disponiveis.exclude(data_nascimento__isnull=True)
        .values_list('data_nascimento__year', flat=True).distinct()
    )
    return render(request, 'imperios/imperio.html', {
        'imperio': imperio,
        'adolescentes': membros,
        'disponiveis': disponiveis,
        'anos_nascimento_disponiveis': anos_nascimento_disponiveis,
        'readonly': readonly,
        'ano_selecionado': ano,
    })


@login_required
@require_http_methods(["POST"])
def bulk_add_imperio(request, imperio_id):
    """Adicionar múltiplos adolescentes a um Império via AJAX"""
    if is_ano_readonly(request):
        return JsonResponse({'ok': False, 'error': 'Ano somente leitura'}, status=403)
    imperio = get_object_or_404(Imperio, id=imperio_id)
    data = json.loads(request.body)
    ids = data.get('ids', [])
    count = Adolescente.objects.filter(id__in=ids, ano=imperio.ano).update(imperio=imperio)
    return JsonResponse({'ok': True, 'count': count})


@login_required
@require_http_methods(["POST"])
def bulk_remove_imperio(request, imperio_id):
    """Remover múltiplos adolescentes de um Império via AJAX"""
    if is_ano_readonly(request):
        return JsonResponse({'ok': False, 'error': 'Ano somente leitura'}, status=403)
    imperio = get_object_or_404(Imperio, id=imperio_id)
    data = json.loads(request.body)
    ids = data.get('ids', [])
    count = Adolescente.objects.filter(id__in=ids, imperio=imperio).update(imperio=None)
    return JsonResponse({'ok': True, 'count': count})


def exportar_adolescentes_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="adolescentes.csv"'

    writer = csv.writer(response)
    writer.writerow(['Nome', 'Sobrenome', 'Data de Nascimento', 'Sexo', 'PG', 'Império'])

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
    
    # Filtrar por ano selecionado
    ano = get_ano_selecionado(request)
    readonly = is_ano_readonly(request)
    
    # Filtros de data
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    dia_especifico = request.GET.get('dia_especifico')
    
    # Estatísticas básicas - filtradas por ano
    total_adolescentes = Adolescente.objects.filter(ano=ano).count()
    total_pgs = PequenoGrupo.objects.filter(ano=ano).count()
    total_imperios = Imperio.objects.filter(ano=ano).count()
    total_eventos = DiaEvento.objects.filter(ano=ano).count()
    
    # Filtrar eventos por período se especificado - base filtrada por ano
    eventos_query = DiaEvento.objects.filter(ano=ano)
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
    
    # Distribuição por gênero - filtrada por ano
    generos = Adolescente.objects.filter(ano=ano).values('genero').annotate(
        total=Count('id')
    ).order_by('genero')
    
    genero_labels = []
    genero_data = []
    for genero in generos:
        genero_labels.append(genero['genero'])
        genero_data.append(genero['total'])
    
    # Presença média por PG (top 5) - filtrada por ano
    if eventos_query.exists():
        presenca_por_pg = PequenoGrupo.objects.filter(ano=ano).annotate(
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
        visitantes = ContagemVisitantes.objects.filter(dia=evento).values_list('quantidade_visitantes', flat=True).first() or 0
        # Calcular percentual em relação ao total de adolescentes cadastrados
        percentual = round((presentes / max(total_adolescentes, 1)) * 100, 1)
        presenca_por_evento.append({
            'data': evento.data.strftime('%d/%m'),
            'titulo': evento.titulo or '',
            'presentes': presentes,
            'visitantes': visitantes,
            'total': total,
            'percentual': percentual
        })
    
    # Presença média por Império - filtrada por ano
    if eventos_query.exists():
        presenca_por_imperio = Imperio.objects.filter(ano=ano).annotate(
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
        media_a = contagens.aggregate(avg=Avg('quantidade_pessoas'))['avg']
        contagem_auditorio_media = round(media_a or 0, 1)
        # Última contagem
        ultima_contagem = contagens.order_by('-dia__data').first()
        if ultima_contagem:
            contagem_auditorio_ultimo = ultima_contagem.quantidade_pessoas
            contagem_auditorio_ultimo_usuario = ultima_contagem.usuario_registro.username
            contagem_auditorio_ultimo_data = ultima_contagem.dia.data

    # Contagem de visitantes por evento (média)
    contagem_visitantes_media = 0
    if eventos_query.exists():
        contagens_visitantes = ContagemVisitantes.objects.filter(dia__in=eventos_query)
        media_v = contagens_visitantes.aggregate(avg=Avg('quantidade_visitantes'))['avg']
        contagem_visitantes_media = round(media_v or 0, 1)

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
        
        # Ano selecionado
        'ano_selecionado': ano,
        'anos_disponiveis': ANOS_DISPONIVEIS,
        'readonly': readonly,
        
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
        'contagem_visitantes_media': contagem_visitantes_media,
    }
    
    return render(request, 'adolescentes/dashboard.html', context)

@permission_required('adolescentes.add_contagemauditorio', raise_exception=True)
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