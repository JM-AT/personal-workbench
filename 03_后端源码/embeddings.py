"""可插拔文本嵌入：hash（离线）/ openai（含 Ollama 兼容）/ fastembed。"""
import hashlib
import re

import numpy as np


class Embedder:
    def __init__(self, embedding_cfg: dict):
        self.cfg = embedding_cfg or {}
        self.provider = (self.cfg.get("provider") or "hash").lower()
        self.dim = int(self.cfg.get("dim", 256))
        self._fastembed = None

    # ---- hash 嵌入：基于词元哈希的词袋向量，纯离线，适合演示 ----
    def _hash_embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for token in re.findall(r"\w+", text.lower()):
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        n = np.linalg.norm(vec)
        if n > 0:
            vec = vec / n
        return vec

    # ---- OpenAI 兼容嵌入（也覆盖 Ollama 的 /v1/embeddings）----
    def _openai_embed(self, texts):
        from openai import OpenAI

        client = OpenAI(
            base_url=self.cfg.get("base_url") or None,
            api_key=self.cfg.get("api_key") or "EMPTY",
        )
        resp = client.embeddings.create(model=self.cfg.get("model"), input=texts)
        return [np.array(d.embedding, dtype=np.float32) for d in resp.data]

    # ---- fastembed 本地模型（首次使用会下载小模型）----
    def _fastembed_embed(self, texts):
        from fastembed import TextEmbedding

        if self._fastembed is None:
            self._fastembed = TextEmbedding(
                model_name=self.cfg.get("model") or "BAAI/bge-small-zh-v1.5"
            )
        return [np.array(v, dtype=np.float32) for v in self._fastembed.embed(texts)]

    def embed(self, text: str) -> np.ndarray:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts):
        if self.provider == "openai":
            return self._openai_embed(texts)
        if self.provider == "fastembed":
            try:
                return self._fastembed_embed(texts)
            except Exception:
                self.provider = "hash"
                return [self._hash_embed(t) for t in texts]
        # 默认 / 兜底
        return [self._hash_embed(t) for t in texts]
