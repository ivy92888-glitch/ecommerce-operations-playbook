"""
Ecommerce Operations Assistant — 知识库优先 + DuckDuckGo 上网兜底
侧边栏：入口选择（亚马逊 / 独立站）→ 切换时加载对应独立知识库
"""
import os, sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag import EcomChatbot

st.set_page_config(page_title="Ecommerce Operations Assistant", page_icon="🛒", layout="wide")

def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODE_LABELS = {
    "amazon": "亚马逊",
    "dropshipping": "独立站",
}

# Init — only once per mode
if "chatbot" not in st.session_state:
    st.session_state.chatbot = EcomChatbot(base_dir=get_base_dir(), mode="amazon")
    st.session_state._prev_mode = "amazon"
    st.session_state.messages = []

with st.sidebar:
    st.title("🛒 Ecommerce Assistant")
    st.caption("跨境电商运营问答助手")
    
    st.divider()
    
    st.subheader("选择入口")
    mode = st.radio("入口", options=["amazon", "dropshipping"], 
                     format_func=lambda x: MODE_LABELS[x],
                     key="mode_selector")
    
    # Rebuild chatbot when mode changes (different knowledge base!)
    if mode != st.session_state._prev_mode:
        st.session_state.chatbot = EcomChatbot(base_dir=get_base_dir(), mode=mode)
        st.session_state._prev_mode = mode
        st.session_state.messages = []
        st.rerun()
    
    status = st.session_state.chatbot.get_status()
    st.info(f"📚 {MODE_LABELS[mode]}知识库 {status['knowledge_chunks']} 条\n🌐 上网兜底: {'开启' if status['web_fallback'] else '关闭'}")
    
    st.divider()
    
    with st.expander("API 设置", expanded=False):
        base_url = st.text_input("Base URL", value=os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1"))
        api_key = st.text_input("API Key", value=os.environ.get("LLM_API_KEY", ""), type="password")
        model = st.text_input("Model", value=os.environ.get("LLM_MODEL", "deepseek-ai/DeepSeek-V3"))
        os.environ["LLM_BASE_URL"] = base_url
        os.environ["LLM_API_KEY"] = api_key
        os.environ["LLM_MODEL"] = model
    
    top_k = st.slider("Top-K", min_value=2, max_value=10, value=5)
    st.session_state.chatbot.top_k = top_k
    
    web_fb = st.checkbox("上网兜底（知识库没命中时自动搜）", value=status['web_fallback'])
    st.session_state.chatbot.web_fallback = web_fb

# Title based on mode
st.title(f"🛒 {MODE_LABELS[mode]}运营助手")

if not st.session_state.messages:
    st.info(f"👋 你好！我是{MODE_LABELS[mode]}运营专家。没命中的问题会自动上网搜权威结果。")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("参考来源"):
                for src in msg["sources"]:
                    st.write(f"- {src}")

if prompt := st.chat_input("提问..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.spinner("检索知识库..."):
        retrieved = st.session_state.chatbot.retrieve(prompt)
    
    top_score = retrieved[0][2] if retrieved else 0
    use_web = st.session_state.chatbot.web_fallback and (top_score < 0.25 or len(retrieved) < 2)
    
    web_results = None
    if use_web:
        with st.spinner("知识库命中不高，同时上网搜索..."):
            web_results = st.session_state.chatbot.web_search(prompt)
    
    with st.chat_message("assistant"):
        try:
            stream = st.session_state.chatbot.stream_llm(prompt, knowledge_results=retrieved, web_results=web_results)
            
            full_response = ""
            placeholder = st.empty()
            for chunk in stream:
                full_response += chunk
                placeholder.markdown(full_response)
            
            sources = []
            for _, src, score in retrieved:
                if score > 0.08:
                    sources.append(f"知识库: {src} (相关度 {score:.2f})")
            if use_web and web_results:
                for r in web_results[:3]:
                    s = f"网页: {r.get('title', '')}"
                    if r.get('url'):
                        s += f" ({r['url'][:60]})"
                    sources.append(s)
            
            mode_hint = ""
            if top_score < 0.08:
                mode_hint = "\n\n*（知识库未命中，基于网页搜索结果回答）*"
            elif use_web:
                mode_hint = "\n\n*（知识库 + 网页搜索综合回答）*"
            
            placeholder.markdown(full_response + mode_hint)
            
            if sources:
                with st.expander("参考来源"):
                    for s in sources:
                        st.write(f"- {s}")
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response, 
                "sources": sources,
            })
        except Exception as e:
            st.error(f"出错了：{str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": f"抱歉：{str(e)}"})
