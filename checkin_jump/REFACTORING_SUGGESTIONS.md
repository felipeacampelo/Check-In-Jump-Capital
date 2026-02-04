# Sugestões de Refatoração e Melhorias

## 📋 Índice
1. [Padrões de Projeto](#padrões-de-projeto)
2. [Separação de Responsabilidades](#separação-de-responsabilidades)
3. [Otimizações de Performance](#otimizações-de-performance)
4. [Melhorias de Código](#melhorias-de-código)
5. [Prioridades de Implementação](#prioridades-de-implementação)

---

## 🎯 Padrões de Projeto

### 1. **Service Layer Pattern**
**Problema:** Views muito grandes com lógica de negócio misturada

**Solução:** Criar camada de serviços

```python
# adolescentes/services.py (NOVO ARQUIVO)

class DiaEventoService:
    """Serviço para lógica de negócio relacionada a eventos"""
    
    @staticmethod
    def calcular_estatisticas_dia(dia):
        """Calcula estatísticas de um dia específico"""
        contagem_auditorio = dia.contagens_auditorio.first()
        total_checkin = Presenca.objects.filter(dia=dia, presente=True).count()
        
        return {
            'total_presentes': contagem_auditorio.quantidade_pessoas if contagem_auditorio else total_checkin,
            'fonte': 'auditorio' if contagem_auditorio else 'checkin',
            'total_checkin': total_checkin
        }
    
    @staticmethod
    def calcular_media_auditorio(dias_queryset):
        """Calcula média baseada em contagens de auditório"""
        total_contagens = 0
        soma_pessoas = 0
        
        for dia in dias_queryset:
            contagem = dia.contagens_auditorio.first()
            if contagem:
                soma_pessoas += contagem.quantidade_pessoas
                total_contagens += 1
        
        return soma_pessoas / total_contagens if total_contagens > 0 else 0


class PGVIPService:
    """Serviço para lógica do PG VIP"""
    
    @staticmethod
    def obter_candidatos_pg_vip(dia):
        """Retorna candidatos para PG VIP e lista de pessoas para alocar"""
        presentes_ids = Presenca.objects.filter(
            dia=dia, presente=True
        ).values_list('adolescente_id', flat=True)
        
        presentes_sem_pg = Adolescente.objects.filter(
            id__in=presentes_ids,
            pg__isnull=True
        ).annotate(
            total_presencas=Count('presenca', filter=Q(presenca__presente=True))
        ).order_by('total_presencas', 'nome', 'sobrenome')
        
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
        
        return pg_vip_candidatos, precisa_alocar


class PaginacaoService:
    """Serviço genérico para paginação"""
    
    @staticmethod
    def paginar(queryset, request, items_per_page=20):
        """Pagina um queryset"""
        paginator = Paginator(queryset, items_per_page)
        page = request.GET.get('page')
        
        try:
            return paginator.page(page)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)
```

**Uso nas views:**
```python
@login_required
def lista_dias_evento(request):
    dias_list = DiaEvento.objects.prefetch_related('contagens_auditorio').order_by('-data')
    
    # Anotar estatísticas
    for dia in dias_list:
        stats = DiaEventoService.calcular_estatisticas_dia(dia)
        dia.total_presentes = stats['total_presentes']
        dia.fonte = stats['fonte']
        dia.total_presentes_checkin = stats['total_checkin']
    
    media_presentes = DiaEventoService.calcular_media_auditorio(dias_list)
    dias = PaginacaoService.paginar(dias_list, request, 20)
    
    return render(request, 'checkin/lista_dias.html', {
        'dias': dias,
        'media_presentes': media_presentes,
        'pode_adicionar_dia': request.user.has_perm('adolescentes.add_diaevento'),
    })
```

---

### 2. **Repository Pattern**
**Problema:** Queries complexas espalhadas pelas views

**Solução:** Criar repositories para encapsular queries

```python
# adolescentes/repositories.py (NOVO ARQUIVO)

class AdolescenteRepository:
    """Repository para queries de Adolescente"""
    
    @staticmethod
    def buscar_com_presencas_otimizado():
        """Retorna adolescentes com presenças otimizadas"""
        return Adolescente.objects.select_related('pg', 'imperio').prefetch_related(
            Prefetch(
                'presenca_set',
                queryset=Presenca.objects.select_related('dia').order_by('-dia__data')[:10],
                to_attr='ultimas_presencas'
            )
        )
    
    @staticmethod
    def buscar_por_nome(queryset, termo_busca):
        """Busca inteligente por nome"""
        if not termo_busca:
            return queryset
        
        palavras = [p.strip() for p in termo_busca.split() if p.strip()]
        if not palavras:
            return queryset
        
        if len(palavras) == 1:
            return queryset.filter(
                Q(nome__icontains=palavras[0]) | Q(sobrenome__icontains=palavras[0])
            )
        
        nome_completo = ' '.join(palavras)
        nome_invertido = ' '.join(palavras[::-1])
        
        query = (
            Q(nome__icontains=nome_completo) |
            Q(sobrenome__icontains=nome_completo) |
            Q(nome__icontains=nome_invertido) |
            Q(sobrenome__icontains=nome_invertido)
        )
        
        # Busca por todas as palavras
        query_palavras = Q()
        for palavra in palavras:
            query_palavras &= (Q(nome__icontains=palavra) | Q(sobrenome__icontains=palavra))
        query |= query_palavras
        
        return queryset.filter(query)


class PresencaRepository:
    """Repository para queries de Presença"""
    
    @staticmethod
    def obter_presentes_do_dia(dia):
        """Retorna IDs dos presentes em um dia"""
        return Presenca.objects.filter(
            dia=dia, presente=True
        ).values_list('adolescente_id', flat=True)
    
    @staticmethod
    def contar_presencas_por_adolescente(adolescente):
        """Conta total de presenças de um adolescente"""
        return Presenca.objects.filter(
            adolescente=adolescente, presente=True
        ).count()
```

---

### 3. **Manager Customizado**
**Problema:** Queries repetidas em vários lugares

**Solução:** Adicionar managers customizados nos models

```python
# adolescentes/models.py

class DiaEventoManager(models.Manager):
    """Manager customizado para DiaEvento"""
    
    def com_estatisticas(self):
        """Retorna dias com estatísticas anotadas"""
        return self.prefetch_related('contagens_auditorio').annotate(
            total_presentes_checkin=Count('presenca', filter=Q(presenca__presente=True))
        )
    
    def ultimos_eventos(self, limite=10):
        """Retorna últimos eventos ordenados por data"""
        return self.com_estatisticas().order_by('-data')[:limite]


class DiaEvento(models.Model):
    # ... campos existentes ...
    
    objects = DiaEventoManager()  # Manager customizado
    
    def get_contagem_principal(self):
        """Retorna contagem principal (auditório se disponível, senão check-in)"""
        contagem_auditorio = self.contagens_auditorio.first()
        if contagem_auditorio:
            return {
                'valor': contagem_auditorio.quantidade_pessoas,
                'fonte': 'auditorio'
            }
        
        total_checkin = self.presenca_set.filter(presente=True).count()
        return {
            'valor': total_checkin,
            'fonte': 'checkin'
        }
```

---

## 🔧 Separação de Responsabilidades

### 4. **Mixins para Views**
**Problema:** Código duplicado em várias views

```python
# adolescentes/mixins.py (NOVO ARQUIVO)

class PaginacaoMixin:
    """Mixin para adicionar paginação a views"""
    paginate_by = 20
    
    def paginar_queryset(self, queryset):
        return PaginacaoService.paginar(queryset, self.request, self.paginate_by)


class PermissaoMixin:
    """Mixin para verificar permissões"""
    required_permission = None
    
    def dispatch(self, request, *args, **kwargs):
        if self.required_permission and not request.user.has_perm(self.required_permission):
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('pagina_inicial')
        return super().dispatch(request, *args, **kwargs)
```

---

### 5. **Form Helpers**
**Problema:** Lógica de formulário nas views

```python
# adolescentes/form_helpers.py (NOVO ARQUIVO)

class AdolescenteFormHelper:
    """Helper para processar formulários de adolescente"""
    
    @staticmethod
    def processar_criacao(form, request, dia_id=None):
        """Processa criação de adolescente com check-in automático"""
        if form.cleaned_data['data_nascimento'] > datetime.now().date():
            return False, "A data de nascimento não pode ser no futuro."
        
        adolescente = form.save()
        
        if dia_id:
            try:
                dia = DiaEvento.objects.get(id=dia_id)
                Presenca.objects.update_or_create(
                    adolescente=adolescente,
                    dia=dia,
                    defaults={'presente': True}
                )
                return True, f"Adolescente {adolescente.nome} criado e check-in confirmado!"
            except DiaEvento.DoesNotExist:
                return True, "Adolescente criado, mas não foi possível fazer o check-in automático."
        
        return True, "Adolescente criado com sucesso!"
```

---

## ⚡ Otimizações de Performance

### 6. **Caching**
**Problema:** Queries repetidas para dados que mudam pouco

```python
# adolescentes/cache_utils.py (NOVO ARQUIVO)

from django.core.cache import cache
from django.conf import settings

class CacheHelper:
    """Helper para gerenciar cache"""
    
    TIMEOUT_CURTO = 300  # 5 minutos
    TIMEOUT_MEDIO = 1800  # 30 minutos
    TIMEOUT_LONGO = 3600  # 1 hora
    
    @staticmethod
    def get_or_set(key, callable_func, timeout=TIMEOUT_MEDIO):
        """Obtém do cache ou executa função e armazena"""
        data = cache.get(key)
        if data is None:
            data = callable_func()
            cache.set(key, data, timeout)
        return data
    
    @staticmethod
    def invalidar_cache_dia(dia_id):
        """Invalida cache relacionado a um dia específico"""
        cache.delete(f'dia_{dia_id}_stats')
        cache.delete(f'dia_{dia_id}_pg_vip')
        cache.delete('lista_dias_media')


# Uso nas views:
def lista_dias_evento(request):
    def calcular_media():
        # ... lógica de cálculo ...
        return media
    
    media_presentes = CacheHelper.get_or_set(
        'lista_dias_media',
        calcular_media,
        CacheHelper.TIMEOUT_MEDIO
    )
```

---

### 7. **Bulk Operations**
**Problema:** N+1 queries ao processar múltiplos registros

```python
# Ao invés de:
for dia in dias_list:
    dia.total_presentes_checkin = Presenca.objects.filter(dia=dia, presente=True).count()

# Fazer:
from django.db.models import Count, Subquery, OuterRef

dias_list = DiaEvento.objects.annotate(
    total_presentes_checkin=Count('presenca', filter=Q(presenca__presente=True))
).prefetch_related('contagens_auditorio')
```

---

## 📝 Melhorias de Código

### 8. **Constants e Enums**
**Problema:** Strings mágicas espalhadas pelo código

```python
# adolescentes/constants.py (NOVO ARQUIVO)

from enum import Enum

class FiltroPresenca(Enum):
    TODOS = 'todos'
    PRESENTES = 'presentes'
    AUSENTES = 'ausentes'

class FonteContagem(Enum):
    AUDITORIO = 'auditorio'
    CHECKIN = 'checkin'

# Configurações
ITEMS_PER_PAGE = 20
MAX_PRESENCAS_PG_VIP = 3
MAX_ULTIMAS_PRESENCAS = 10
```

---

### 9. **Type Hints**
**Problema:** Falta de tipagem dificulta manutenção

```python
from typing import List, Dict, Optional, Tuple
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse

def buscar_adolescentes_por_nome(
    queryset: QuerySet[Adolescente], 
    termo_busca: str
) -> QuerySet[Adolescente]:
    """Busca adolescentes por nome"""
    ...

def calcular_estatisticas_dia(dia: DiaEvento) -> Dict[str, any]:
    """Calcula estatísticas de um dia"""
    ...
```

---

### 10. **Validators Customizados**
**Problema:** Validações espalhadas pelas views

```python
# adolescentes/validators.py (NOVO ARQUIVO)

from django.core.exceptions import ValidationError
from datetime import date

def validar_data_nascimento_futura(value: date) -> None:
    """Valida que data de nascimento não é futura"""
    if value > date.today():
        raise ValidationError('A data de nascimento não pode ser no futuro.')

def validar_quantidade_positiva(value: int) -> None:
    """Valida que quantidade é positiva"""
    if value <= 0:
        raise ValidationError('A quantidade deve ser maior que zero.')


# No model:
class Adolescente(models.Model):
    data_nascimento = models.DateField(
        validators=[validar_data_nascimento_futura]
    )
```

---

## 🎯 Prioridades de Implementação

### **Prioridade ALTA** (Impacto imediato)
1. ✅ **Service Layer** - Reduz complexidade das views
2. ✅ **Repository Pattern** - Centraliza queries
3. ✅ **Constants** - Elimina strings mágicas
4. ✅ **Bulk Operations** - Melhora performance

### **Prioridade MÉDIA** (Melhoria gradual)
5. ⚠️ **Managers Customizados** - Queries reutilizáveis
6. ⚠️ **Form Helpers** - Lógica de formulário organizada
7. ⚠️ **Type Hints** - Melhor manutenibilidade
8. ⚠️ **Validators** - Validações consistentes

### **Prioridade BAIXA** (Nice to have)
9. 💡 **Caching** - Otimização adicional
10. 💡 **Mixins** - Reutilização de código

---

## 📦 Estrutura de Arquivos Sugerida

```
adolescentes/
├── models.py
├── views.py (reduzido)
├── forms.py
├── urls.py
├── admin.py
├── services/          # NOVO
│   ├── __init__.py
│   ├── dia_evento_service.py
│   ├── pg_vip_service.py
│   └── paginacao_service.py
├── repositories/      # NOVO
│   ├── __init__.py
│   ├── adolescente_repository.py
│   └── presenca_repository.py
├── utils/             # NOVO
│   ├── __init__.py
│   ├── cache_helper.py
│   ├── form_helpers.py
│   └── validators.py
├── constants.py       # NOVO
└── mixins.py          # NOVO
```

---

## 🚀 Exemplo de Refatoração Completa

### **ANTES** (view atual):
```python
@login_required
def lista_dias_evento(request):
    dias_list = DiaEvento.objects.prefetch_related('contagens_auditorio').order_by('-data')
    
    total_contagens = 0
    soma_pessoas = 0
    
    for dia in dias_list:
        dia.total_presentes_checkin = Presenca.objects.filter(dia=dia, presente=True).count()
        contagem_auditorio = dia.contagens_auditorio.first()
        if contagem_auditorio:
            dia.total_presentes = contagem_auditorio.quantidade_pessoas
            dia.fonte = 'auditorio'
            soma_pessoas += contagem_auditorio.quantidade_pessoas
            total_contagens += 1
        else:
            dia.total_presentes = dia.total_presentes_checkin
            dia.fonte = 'checkin'
    
    media_presentes = soma_pessoas / total_contagens if total_contagens > 0 else 0
    
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
        'pode_adicionar_dia': request.user.has_perm('adolescentes.add_diaevento'),
    })
```

### **DEPOIS** (refatorado):
```python
@login_required
def lista_dias_evento(request: HttpRequest) -> HttpResponse:
    """Lista dias de evento com estatísticas e paginação"""
    # Buscar dias com estatísticas
    dias_list = DiaEvento.objects.com_estatisticas()
    
    # Anotar dados calculados
    for dia in dias_list:
        stats = DiaEventoService.calcular_estatisticas_dia(dia)
        dia.total_presentes = stats['total_presentes']
        dia.fonte = stats['fonte']
    
    # Calcular média
    media_presentes = DiaEventoService.calcular_media_auditorio(dias_list)
    
    # Paginar
    dias = PaginacaoService.paginar(dias_list, request, ITEMS_PER_PAGE)
    
    return render(request, 'checkin/lista_dias.html', {
        'dias': dias,
        'media_presentes': media_presentes,
        'pode_adicionar_dia': request.user.has_perm('adolescentes.add_diaevento'),
    })
```

**Benefícios:**
- ✅ View 60% menor
- ✅ Lógica testável separadamente
- ✅ Código reutilizável
- ✅ Type hints para melhor IDE support
- ✅ Mais fácil de manter

---

## 📚 Recursos Adicionais

- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [Django Design Patterns](https://agiliq.com/blog/2013/09/django-design-patterns/)

---

**Nota:** Implementar todas as sugestões de uma vez pode ser overwhelming. Recomendo começar pelos itens de **Prioridade ALTA** e ir evoluindo gradualmente.
