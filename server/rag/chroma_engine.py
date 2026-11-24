import os
from openai import AuthenticationError, OpenAI
from django.conf import settings


class ChromaEngine:
    COLLECTION_NAME = 'drone_docs_openai'

    def __init__(self):
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        self.embedding_model = getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        self.embedding_dim = getattr(settings, 'OPENAI_EMBEDDING_DIM', 1024)
        self.chat_model = getattr(settings, 'OPENAI_MODEL', '') or 'gpt-6-sol'
        self.reasoning_effort = getattr(settings, 'OPENAI_REASONING_EFFORT', 'high')
        self.base_url = getattr(settings, 'OPENAI_BASE_URL', '')
        api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            raise RuntimeError('问答服务未配置，请联系管理员')
        self.client = OpenAI(api_key=api_key, base_url=self.base_url or None)

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
        resp = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
            dimensions=self.embedding_dim,
        )
        return [item.embedding for item in sorted(resp.data, key=lambda item: item.index)]

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
        query_embedding = self._embed(query)[0]
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

    def query(self, question):
        try:
            resp = self.client.responses.create(
                model=self.chat_model,
                input=self._build_messages(question),
                reasoning={'effort': self.reasoning_effort},
                store=False,
            )
            return resp.output_text or ''
        except AuthenticationError as exc:
            raise RuntimeError('API 密钥无效或接口地址不匹配，请检查后端配置') from exc

    def query_stream(self, question):
        try:
            events = self.client.responses.create(
                model=self.chat_model,
                input=self._build_messages(question),
                reasoning={'effort': self.reasoning_effort},
                store=False,
                stream=True,
            )
            for event in events:
                if event.type == 'response.output_text.delta' and event.delta:
                    yield event.delta
                elif event.type == 'error':
                    raise RuntimeError('模型生成失败，请检查中转站接口状态')
                elif event.type == 'response.failed':
                    raise RuntimeError('模型生成失败，请检查中转站接口状态')
        except AuthenticationError as exc:
            raise RuntimeError('API 密钥无效或接口地址不匹配，请检查后端配置') from exc
