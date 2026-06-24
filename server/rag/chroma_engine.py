from http import HTTPStatus
import os
import dashscope
from dashscope import Generation, MultiModalConversation, TextEmbedding
from django.conf import settings


class ChromaEngine:
    COLLECTION_NAME = 'drone_docs'

    def __init__(self):
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        self.embedding_model = getattr(settings, 'DASHSCOPE_EMBEDDING_MODEL', 'text-embedding-v4')
        self.embedding_dim = getattr(settings, 'DASHSCOPE_EMBEDDING_DIM', 1024)
        self.chat_model = os.getenv('DASHSCOPE_MODEL') or getattr(settings, 'DASHSCOPE_MODEL', 'qwen-plus')
        api_key = os.getenv('DASHSCOPE_API_KEY') or getattr(settings, 'DASHSCOPE_API_KEY', '')
        if not api_key:
            raise RuntimeError('缺少 DASHSCOPE_API_KEY 环境变量')
        dashscope.api_key = api_key

    def _get_collection(self):
        import chromadb
        client = chromadb.PersistentClient(path=self.persist_dir)
        return client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={'hnsw:space': 'cosine'},
        )

    def _embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        resp = TextEmbedding.call(
            model=self.embedding_model,
            input=texts,
            dimension=self.embedding_dim,
            text_type='document',
        )
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(f'Embedding 调用失败：{resp.code} {resp.message}')
        embeddings = resp.output['embeddings']
        embeddings.sort(key=lambda x: x['text_index'])
        return [e['embedding'] for e in embeddings]

    def build_index(self):
        from drones.models import DroneDoc
        docs = list(DroneDoc.objects.all().order_by('id'))
        if not docs:
            return False, '没有文档数据，请先执行 python manage.py seed_drones'

        collection = self._get_collection()
        if collection.count():
            collection.delete(where={'category': {'$ne': ''}})

        batch_size = 10
        count = 0
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i + batch_size]
            texts = [d.to_rag_text() for d in batch]
            ids = [str(d.id) for d in batch]
            metadatas = [
                {
                    'title': d.title,
                    'category': d.category,
                    'model_name': d.model_name or '',
                    'tags': d.tags or '',
                }
                for d in batch
            ]
            embeddings = self._embed(texts)
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            count += len(batch)

        return True, f'Chroma 向量索引构建完成，共写入 {count} 条文档'

    def search(self, query, n_results=5):
        collection = self._get_collection()
        if collection.count() == 0:
            return []
        resp = TextEmbedding.call(
            model=self.embedding_model,
            input=[query],
            dimension=self.embedding_dim,
            text_type='query',
        )
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(f'Embedding 调用失败：{resp.code} {resp.message}')
        query_embedding = resp.output['embeddings'][0]['embedding']
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            include=['documents', 'metadatas', 'distances'],
        )
        items = []
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0],
        ):
            items.append({'text': doc, 'meta': meta, 'score': 1 - dist})
        return items

    def _build_messages(self, question):
        chunks = self.search(question, n_results=5)
        if not chunks:
            context = '（知识库暂无相关文档，请先执行索引构建）'
        else:
            context_parts = []
            for i, chunk in enumerate(chunks, 1):
                title = chunk['meta'].get('title', '')
                context_parts.append(f'[文档{i}] {title}\n{chunk["text"]}')
            context = '\n\n---\n\n'.join(context_parts)

        answer_outline = (
            '请尽量按以下结构组织回答：\n'
            '1. 先给出问题判断或结论概览；\n'
            '2. 再解释原因、原理或常见触发条件；\n'
            '3. 给出具体操作步骤，步骤尽量完整；\n'
            '4. 补充实训中的安全风险、注意事项和常见错误；\n'
            '5. 如果适合写入实验报告，再给出可直接记录的要点。\n'
            '若用户问题涉及故障排查，请按照“现象-可能原因-验证方法-处理建议”的顺序展开。'
        )
        system_prompt = (
            '你是一名面向高校实训教学的无人机导师助手，专注于无人机设计、组装、调试、操作、维护、飞行安全和实验报告指导。'
            '请根据下方知识库内容回答用户问题，回答要专业、完整、结构清晰，不要只给简短结论。'
            '请优先结合知识库内容作答，并在合适时引用文档中的关键信息。'
            '若知识库内容不足以回答，请基于无人机专业知识补充说明，同时明确哪些内容属于经验性补充。'
            '回答应兼顾学生可操作性与教师实训场景，尽量体现步骤、原因分析、安全提示和报告记录建议。'
        )
        user_prompt = (
            f'知识库参考内容：\n\n{context}\n\n'
            f'{answer_outline}\n\n'
            f'用户问题：{question}\n\n'
            '请使用较详细的中文回答，适当使用小标题或编号，让学生能够直接按回答完成实训操作或排查。'
        )
        return [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]

    def _extract_response_text(self, response):
        content = response.output.choices[0].message.content
        if isinstance(content, list):
            return content[0].get('text', '')
        return content or ''

    def query(self, question):
        resp = MultiModalConversation.call(
            model=self.chat_model,
            messages=self._build_messages(question),
            temperature=0.3,
            max_tokens=3072,
            enable_thinking=False,
        )
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(f'Generation 调用失败：{resp.code} {resp.message}')
        return self._extract_response_text(resp)

    def query_stream(self, question):
        responses = Generation.call(
            model=self.chat_model,
            messages=self._build_messages(question),
            temperature=0.3,
            max_tokens=3072,
            result_format='message',
            stream=True,
            incremental_output=True,
            enable_thinking=False,
        )
        for resp in responses:
            if resp.status_code != HTTPStatus.OK:
                raise RuntimeError(f'Generation 调用失败：{resp.code} {resp.message}')
            text = self._extract_response_text(resp)
            if text:
                yield text
