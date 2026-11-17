"""
RAG + Web-search Q&A assistant for cross-border e-commerce operations.
- Knowledge base first (TF-IDF retrieval)
- If low confidence → DuckDuckGo web search fallback (free, no API key needed)
"""
import os, re, glob, json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests


class EcomChatbot:
    MODES = {
        "amazon": ("knowledge/amazon", "亚马逊运营"),
        "dropshipping": ("knowledge/dropshipping", "独立站运营"),
    }
    def __init__(self, base_dir=".", mode="amazon", top_k=5, web_fallback=True):
        self.base_dir = base_dir
        self.mode = mode
        self.top_k = top_k
        self.web_fallback = web_fallback
        
        self.chunks = []
        self.sources = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._load_knowledge()
    
    def _scan_dir(self, kb_dir, tag=""):
        chunks, sources = [], []
        if not os.path.exists(kb_dir):
            return chunks, sources
        
        files = sorted(glob.glob(os.path.join(kb_dir, "*.md")))
        for fpath in files:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            fname = os.path.basename(fpath)
            label = f"{tag}/{fname}" if tag else fname
            
            sections = re.split(r'\n(?=## )', content)
            for sec in sections:
                sec = sec.strip()
                if len(sec) > 40:
                    chunks.append(sec)
                    sources.append(label)
        return chunks, sources
    
    def _load_knowledge(self):
        all_chunks, all_sources = [], []
        
        # Only load the selected mode's knowledge base
        if self.mode in self.MODES:
            rel_path, tag = self.MODES[self.mode]
            full = os.path.join(self.base_dir, rel_path)
            if os.path.isdir(full):
                c, s = self._scan_dir(full, tag)
                all_chunks.extend(c)
                all_sources.extend(s)
        
        self.chunks = all_chunks
        self.sources = all_sources
        
        if self.chunks:
            self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), min_df=1)
            self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
        else:
            self.vectorizer = None
            self.tfidf_matrix = None
    
    def retrieve(self, query, k=None):
        """Retrieve top-k knowledge chunks. Returns [(chunk, source, score), ...]"""
        if not self.chunks or self.vectorizer is None:
            return []
        k = k or self.top_k
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_idx = sims.argsort()[-k:][::-1]
        return [(self.chunks[i], self.sources[i], sims[i]) for i in top_idx if sims[i] > 0.05]
    
    def web_search(self, query, max_results=5):
        """DuckDuckGo Instant Answer API (free, no key needed).
        Falls back to DuckDuckGo HTML if no instant answer."""
        results = []
        
        # Try Instant Answer API first
        try:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
                timeout=10
            )
            data = r.json()
            
            # Abstract from Wikipedia/official sources
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "Wikipedia"),
                    "snippet": data["AbstractText"],
                    "url": data.get("AbstractURL", ""),
                    "source": "DuckDuckGo Abstract"
                })
            
            # Related topics
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:60],
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "source": "DuckDuckGo Related"
                    })
        except Exception:
            pass
        
        # Fallback: DuckDuckGo HTML scraping (simple, robust)
        if len(results) < 3:
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                r = requests.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers=headers,
                    timeout=10
                )
                # Parse simple HTML results
                html = r.text
                # Find result blocks
                blocks = re.findall(r'class="result__a"[^>]*>([^<]+)</a>.*?class="result__snippet"[^>]*>(.*?)</a>', 
                                  html, re.DOTALL)
                for title, snippet in blocks[:max_results - len(results)]:
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                    if title and snippet:
                        results.append({
                            "title": title[:80],
                            "snippet": snippet[:300],
                            "url": "",
                            "source": "DuckDuckGo Web"
                        })
            except Exception:
                pass
        
        return results[:max_results]
    
    def stream_llm(self, query, knowledge_results=None, web_results=None, stream=True):
        import os, json
        
        if knowledge_results is None:
            knowledge_results = self.retrieve(query)
        
        # Decide: use knowledge, web, or both
        # If top knowledge score > 0.15 → knowledge is confident enough
        # If top knowledge score < 0.08 → fall back to web
        # Otherwise → combine both
        top_score = knowledge_results[0][2] if knowledge_results else 0
        
        use_knowledge = top_score > 0.08
        use_web = self.web_fallback and (top_score < 0.25 or len(knowledge_results) < 2)
        
        if not use_knowledge and web_results is None:
            web_results = self.web_search(query)
        
        # Build context
        context_parts = []
        sources_info = []
        
        if use_knowledge and knowledge_results:
            for chunk, source, score in knowledge_results:
                context_parts.append(f"[来源: {source}, 相关度: {score:.2f}]\n{chunk}")
                sources_info.append(f"知识库: {source} (相关度 {score:.2f})")
        
        if use_web and web_results:
            for r in web_results[:3]:
                context_parts.append(f"[网页来源: {r.get('source', 'Web')} - {r.get('title', '')}]\n{r.get('snippet', '')}")
                src = f"网页: {r.get('title', '')}"
                if r.get("url"):
                    src += f" ({r['url'][:50]})"
                sources_info.append(src)
        
        context = "\n\n---\n\n".join(context_parts) if context_parts else "(无相关知识)"
        
        # Build system prompt — scope based on mode
        mode_label = self.MODES.get(self.mode, ("", "跨境电商运营"))[1] if self.mode in self.MODES else "跨境电商运营"
        if self.mode == "amazon":
            platform_scope = "亚马逊平台运营"
        elif self.mode == "dropshipping":
            platform_scope = "独立站运营（Shopify / WordPress 等自建站）"
        else:
            platform_scope = "跨境电商运营"
        
        if use_knowledge and use_web:
            instruction = f"优先使用{mode_label}知识库中的信息；如知识库不完整，参考网页搜索结果补充。"
        elif use_knowledge:
            instruction = f"优先使用{mode_label}知识库中的信息，确保准确。"
        else:
            instruction = f"{mode_label}知识库未检索到相关内容，基于网页搜索结果和通用{platform_scope}知识回答。"
        
        system_prompt = f"""你是一位跨境电商运营专家，专注于{platform_scope}的业务知识。

{instruction}

要求：
1. 给出的建议必须合规合法，不提供任何规避监管、刷单刷评、操纵排名的操作建议
2. 涉及平台规则（亚马逊/Shopify/Google）时，说明规则可能变化，建议核实最新官方文档
3. 涉及具体数字（费用、比例、时效）时标注"仅供参考，以实际后台为准"
4. 回答结构清晰，分点列出
5. 如果知识库和网页都没有足够信息，诚实说明并给出通用建议"""

        user_prompt = f"""【参考内容】

{context}

【用户问题】
{query}

请根据以上参考内容，针对用户问题给出合规、准确、结构清晰的回答。"""

        # Call LLM
        base_url = os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        api_key = os.environ.get("LLM_API_KEY", "")
        model = os.environ.get("LLM_MODEL", "deepseek-ai/DeepSeek-V3")

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": stream,
            "max_tokens": 1800,
            "temperature": 0.3,
        }

        resp = requests.post(url, headers=headers, json=body, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"LLM 调用失败 ({resp.status_code}): {resp.text[:500]}")
        resp.encoding = "utf-8"

        if stream:
            # Custom iterable class — yields chunks on demand AND carries extra attrs
            class _StreamResult:
                def __iter__(self):
                    for line in resp.iter_lines(decode_unicode=True):
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
                def __next__(self):
                    return next(iter(self))
                
            result = _StreamResult()
            result.sources = sources_info
            result.top_score = top_score
            result.used_knowledge = use_knowledge
            result.used_web = use_web
            return result
        else:
            result = json.loads(resp.text)["choices"][0]["message"]["content"]
            return {"content": result, "sources": sources_info}
    
    def get_status(self):
        return {
            "knowledge_chunks": len(self.chunks),
            "vectorizer_ready": self.vectorizer is not None,
            "web_fallback": self.web_fallback,
        }
