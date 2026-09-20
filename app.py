"""Streamlit UI cho chatbot RAG về đăng ký học tập HUST."""

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(page_title="HUST RAG Chatbot", page_icon="🎓", layout="wide")


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    st.markdown("#### Nguồn được sử dụng")
    for index, item in enumerate(sources, 1):
        metadata = item["metadata"]
        title = metadata["title"]
        label = f"S{index}"
        with st.expander(f"[{label}] {title}"):
            st.caption(
                f"Source: {metadata['source']} · "
                f"Method: {item['retrieval_method']} · Score: {item['score']:.4f}"
            )
            if metadata.get("url"):
                st.markdown(f"[Mở tài liệu gốc]({metadata['url']})")
            excerpt = item["content"][:800]
            st.markdown(excerpt + ("…" if len(item["content"]) > 800 else ""))


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("HUST RAG Chatbot")
    st.caption("Hỏi đáp về quy chế và đăng ký học tập tại Đại học Bách khoa Hà Nội")
    top_k = st.slider("Số chunks", 3, 10, 5)
    st.info("Câu trả lời chỉ được tạo từ tài liệu nguồn và có citation [S#].")

st.title("Chatbot đăng ký học tập HUST")
st.caption("Hỏi về kế hoạch đăng ký, quy chế đào tạo, học phí và các thông báo liên quan.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []))

query = st.chat_input("Nhập câu hỏi về đăng ký học tập HUST...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm và đối chiếu tài liệu..."):
            result = generate_with_citation(query, top_k)
        st.markdown(result["answer"])
        render_sources(result["sources"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "retrieval_source": result["retrieval_source"],
        }
    )