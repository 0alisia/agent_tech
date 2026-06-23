from django.core.management.base import BaseCommand
from rag.chroma_engine import ChromaEngine

class Command(BaseCommand):
    help = '构建 Chroma 向量索引'

    def handle(self, *args, **options):
        engine = ChromaEngine()
        ok, msg = engine.build_index()
        if ok:
            self.stdout.write(self.style.SUCCESS(msg))
        else:
            self.stdout.write(self.style.ERROR(msg))
