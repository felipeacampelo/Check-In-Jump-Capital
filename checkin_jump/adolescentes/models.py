from django.db import models
from django.contrib.auth.models import User

class PequenoGrupo(models.Model):
    nome = models.CharField(max_length=100)
    genero_pg = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nome

class Imperio(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

class Adolescente(models.Model):
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='fotos/', blank=True, null=True)
    data_nascimento = models.DateField()
    GENERO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Feminino"),
    ]
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True, null=False)
    pg = models.ForeignKey(PequenoGrupo, on_delete=models.SET_NULL, blank=True, null=True, related_name='adolescentes')
    imperio = models.ForeignKey(Imperio, on_delete=models.SET_NULL, null=True, blank=True)
    data_inicio = models.DateField(blank=True, null=True)

    class Meta:
        permissions = [
            ("view_dashboard", "Pode visualizar o dashboard"),
            ("view_pgs_page", "Pode ver página de PGs"),
            ("review_duplicates", "Pode revisar e mesclar duplicados"),
        ]

    def __str__(self):
        return f"{self.nome} {self.sobrenome}"
    
    def ultimas_presencas(self):
        return self.presenca_set.order_by('-dia__data')[:5]

class DiaEvento(models.Model):
    data = models.DateField(unique=True)
    titulo = models.CharField(max_length=200, blank=True, null=True, help_text="Título da celebração (ex: 40 Dias de Generosidade)")

    def __str__(self):
        if self.titulo:
            return f"{self.data.strftime('%d/%m/%Y')} - {self.titulo}"
        return self.data.strftime('%d/%m/%Y')

class Presenca(models.Model):
    adolescente = models.ForeignKey(Adolescente, on_delete=models.CASCADE)
    dia = models.ForeignKey(DiaEvento, on_delete=models.CASCADE)
    presente = models.BooleanField(default=False)
    
    class Meta:
        # Evitar duplicatas e otimizar queries
        unique_together = [('adolescente', 'dia')]
        # Índices para melhorar performance
        indexes = [
            models.Index(fields=['adolescente', 'dia']),
            models.Index(fields=['dia', 'presente']),
            models.Index(fields=['adolescente', 'presente']),
        ]
        ordering = ['-dia', 'adolescente']

class DuplicadoRejeitado(models.Model):
    """Par de perfis marcados como NÃO duplicados (rejeição persistida)."""
    adolescente_a = models.ForeignKey(Adolescente, on_delete=models.CASCADE, related_name='rejeicoes_como_a')
    adolescente_b = models.ForeignKey(Adolescente, on_delete=models.CASCADE, related_name='rejeicoes_como_b')
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = [('adolescente_a', 'adolescente_b')]
        ordering = ['-criado_em']

    def save(self, *args, **kwargs):
        # Garantir ordenação a.id < b.id para unicidade consistente
        if self.adolescente_a_id and self.adolescente_b_id and self.adolescente_a_id > self.adolescente_b_id:
            self.adolescente_a_id, self.adolescente_b_id = self.adolescente_b_id, self.adolescente_a_id
        super().save(*args, **kwargs)

class ContagemAuditorio(models.Model):
    dia = models.ForeignKey(DiaEvento, on_delete=models.CASCADE, related_name='contagens_auditorio')
    quantidade_pessoas = models.PositiveIntegerField(help_text="Número de pessoas contadas no auditório")
    usuario_registro = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário que fez o registro")
    data_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['dia']
        verbose_name = "Contagem de Auditório"
        verbose_name_plural = "Contagens de Auditório"
        ordering = ['-data_registro']
    
    def __str__(self):
        return f"{self.dia} - {self.quantidade_pessoas} pessoas (por {self.usuario_registro.username})"
    
    def get_total_presentes(self):
        """Retorna o total de presentes considerando check-ins individuais + contagem de auditório"""
        checkins_individuals = self.dia.presenca_set.filter(presente=True).count()
        return checkins_individuals + self.quantidade_pessoas


class ContagemVisitantes(models.Model):
    dia = models.ForeignKey(DiaEvento, on_delete=models.CASCADE, related_name='contagens_visitantes')
    quantidade_visitantes = models.PositiveIntegerField(help_text="Número de visitantes no dia")
    usuario_registro = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário que fez o registro")
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['dia']
        verbose_name = "Contagem de Visitantes"
        verbose_name_plural = "Contagens de Visitantes"
        ordering = ['-data_registro']

    def __str__(self):
        return f"{self.dia} - {self.quantidade_visitantes} visitantes (por {self.usuario_registro.username})"
