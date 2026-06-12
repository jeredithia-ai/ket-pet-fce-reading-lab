from __future__ import annotations

import os

import streamlit as st

from app import (
    LEVEL_BRIDGE,
    VOCAB,
    build_exercises,
    generate_illustration_image,
    grade,
    make_text,
    make_title,
    select_words,
)


def load_streamlit_secrets() -> None:
    for key in ["IMAROUTER_API_KEY", "IMAGE_API_URL", "IMAGE_MODEL", "IMAGE_SIZE"]:
        try:
            value = st.secrets.get(key)
        except Exception:
            value = None
        if value:
            os.environ.setdefault(key, str(value))


def init_state() -> None:
    st.session_state.setdefault("reading", None)
    st.session_state.setdefault("answers", {})
    st.session_state.setdefault("result", None)


def generate_reading(level: str, mode: str, theme: str | None) -> dict:
    bridge = LEVEL_BRIDGE[level]
    selected_theme = theme or bridge["themes"][0]
    words = select_words(level, 12)
    paragraphs = make_text(level, mode, words, selected_theme)
    reading_id = os.urandom(8).hex()
    image = generate_illustration_image(reading_id, level, mode, selected_theme, paragraphs)
    return {
        "id": reading_id,
        "level": level,
        "mode": mode,
        "title": make_title(level, mode, selected_theme),
        "theme": selected_theme,
        "bridge": bridge,
        "target_words": [w["word"] for w in words],
        "word_bank": words,
        "paragraphs": paragraphs,
        "exercises": build_exercises(level, mode, paragraphs, words),
        "image_url": image["image_url"],
        "image_status": image["image_status"],
        "illustration_prompt": image["illustration_prompt"],
    }


def highlight_words(text: str, words: list[str]) -> str:
    output = text
    for word in words:
        output = output.replace(
            word,
            f"<span style='background:#fff1a8;color:#0c76bf;font-weight:800;padding:0 3px;border-radius:4px'>{word}</span>",
        )
    return output


def render_home() -> None:
    st.title("分级英语词汇绘本阅读与练习系统")
    st.caption("KET / PET / FCE 分级阅读 + Worksheet + 自测复盘")

    col1, col2, col3 = st.columns(3)
    with col1:
        level = st.selectbox("考级等级", ["KET", "PET", "FCE"])
    with col2:
        mode_label = st.selectbox("内容模式", ["绘本故事模式", "标准阅读文章模式"])
        mode = "picture" if mode_label == "绘本故事模式" else "reading"
    with col3:
        theme = st.text_input("主题（可选）", placeholder="如 School life / Animal helpers")

    st.markdown("### KET / PET / FCE 等级匹配图")
    c1, c2, c3 = st.columns(3)
    c1.info("**KET · A2**\n\n基础阅读：短句绘本 / 生活主题 / 词义匹配")
    c2.success("**PET · B1**\n\n进阶阅读：段落阅读 / 观点表达 / 句型改写")
    c3.warning("**FCE · B2**\n\n高阶阅读：多文体 / 推断评价 / 写作输出")

    if st.button("一键生成素材", type="primary"):
        with st.spinner("正在生成阅读、练习和真实配图，生图可能需要 30-90 秒..."):
            st.session_state.reading = generate_reading(level, mode, theme.strip() or None)
            st.session_state.answers = {}
            st.session_state.result = None
        st.rerun()


def render_reading() -> None:
    reading = st.session_state.reading
    if not reading:
        st.info("请先在首页生成一篇阅读。")
        return

    st.header(reading["title"])
    bridge = reading["bridge"]
    st.caption(f"{reading['level']} {bridge['cefr']} · {bridge['stage']}：{bridge['lesson_idea']}")

    if reading["image_url"]:
        st.image(reading["image_url"], use_container_width=True)
    else:
        st.warning(f"图片暂未生成：{reading['image_status']}")

    st.markdown("#### 本篇核心词汇")
    st.write(" · ".join(reading["target_words"]))

    for paragraph in reading["paragraphs"]:
        st.markdown(highlight_words(paragraph, reading["target_words"]), unsafe_allow_html=True)


def render_exercises() -> None:
    reading = st.session_state.reading
    if not reading:
        st.info("请先生成阅读。")
        return

    st.header("Worksheet 专属练习")
    answers = {}
    for ex in reading["exercises"]:
        st.subheader(ex["title"])
        st.write(ex["prompt"])
        if ex["type"] == "matching":
            answers[ex["id"]] = {}
            meanings = [item["meaning"] for item in ex["items"]]
            for item in ex["items"]:
                answers[ex["id"]][item["word"]] = st.selectbox(
                    item["word"],
                    [""] + meanings,
                    key=f"{ex['id']}-{item['word']}",
                )
        elif ex["type"] in {"cloze", "mcq"}:
            answers[ex["id"]] = st.radio(ex["title"], ex["options"], key=ex["id"], label_visibility="collapsed")
        elif ex["type"] == "true_false":
            answers[ex["id"]] = st.radio(ex["title"], [True, False], key=ex["id"], label_visibility="collapsed")
        else:
            answers[ex["id"]] = st.text_input("请输入答案", key=ex["id"])

    if st.button("提交批改", type="primary"):
        st.session_state.result = grade(reading, answers)
        st.rerun()


def render_result() -> None:
    result = st.session_state.result
    if not result:
        st.info("完成练习并提交后，这里会显示结果。")
        return

    st.header("自测考评结果")
    st.metric("正确率", f"{result['percent']}%", f"{result['score']}/{result['total']}")
    st.subheader(result["rating"])
    st.markdown("#### 薄弱词汇")
    st.write(" · ".join(result["weakWords"]))

    st.markdown("#### 错题复盘")
    for item in result["details"]:
        with st.expander(f"{'✓' if item['correct'] else '×'} {item['title']}", expanded=not item["correct"]):
            st.write("你的答案：", item["yourAnswer"])
            st.write("正确答案：", item["answer"])
            st.write(item["explanation"])


load_streamlit_secrets()
init_state()

st.set_page_config(page_title="KET/PET/FCE Reading Lab", page_icon="📘", layout="wide")

tabs = st.tabs(["首页", "阅读", "练习", "结果"])
with tabs[0]:
    render_home()
with tabs[1]:
    render_reading()
with tabs[2]:
    render_exercises()
with tabs[3]:
    render_result()
