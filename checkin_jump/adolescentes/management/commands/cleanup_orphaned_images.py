import os
from django.core.management.base import BaseCommand
from django.conf import settings
from adolescentes.models import Adolescente

class Command(BaseCommand):
    help = 'Limpa referências órfãs de imagens que não existem mais no sistema de arquivos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra quais referências seriam limpas, sem fazer alterações',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra informações detalhadas sobre o processo',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Iniciando limpeza de referências órfãs de imagens...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  Modo DRY-RUN ativo - nenhuma alteração será feita')
            )
        
        # Buscar todos os adolescentes que têm foto definida
        adolescentes_com_foto = Adolescente.objects.exclude(foto='').exclude(foto__isnull=True)
        total_com_foto = adolescentes_com_foto.count()
        
        self.stdout.write(f'📊 Encontrados {total_com_foto} adolescentes com referência de foto')
        
        orphaned_count = 0
        cleaned_count = 0
        
        for adolescente in adolescentes_com_foto:
            try:
                # Verificar se o arquivo existe fisicamente
                file_path = os.path.join(settings.MEDIA_ROOT, adolescente.foto.name)
                
                if not os.path.exists(file_path):
                    orphaned_count += 1
                    
                    if verbose:
                        self.stdout.write(
                            f'🔗 Referência órfã encontrada: {adolescente.nome} {adolescente.sobrenome} -> {adolescente.foto.name}'
                        )
                    
                    if not dry_run:
                        # Limpar a referência órfã
                        adolescente.foto = None
                        adolescente.save(update_fields=['foto'])
                        cleaned_count += 1
                        
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Limpeza realizada para: {adolescente.nome} {adolescente.sobrenome}')
                            )
                
                elif verbose:
                    self.stdout.write(
                        f'✅ Arquivo OK: {adolescente.nome} {adolescente.sobrenome} -> {adolescente.foto.name}'
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao processar {adolescente.nome} {adolescente.sobrenome}: {str(e)}')
                )
        
        # Relatório final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📋 RELATÓRIO FINAL:'))
        self.stdout.write(f'📊 Total de adolescentes com foto: {total_com_foto}')
        self.stdout.write(f'🔗 Referências órfãs encontradas: {orphaned_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Referências que SERIAM limpas: {orphaned_count}')
            )
            self.stdout.write(
                self.style.WARNING('💡 Execute sem --dry-run para aplicar as limpezas')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Referências limpas com sucesso: {cleaned_count}')
            )
        
        if orphaned_count == 0:
            self.stdout.write(
                self.style.SUCCESS('🎉 Nenhuma referência órfã encontrada! Sistema limpo.')
            )
        
        self.stdout.write('='*50)
