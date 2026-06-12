from __future__ import annotations

import os

import streamlit as st

from app import (
    LEVEL_BRIDGE,
    build_exercises,
    generate_illustration_image,
    grade,
    make_text,
    make_title,
    select_words,
)


st.set_page_config(page_title="KET/PET/FCE Reading Lab", page_icon="📘", layout="wide")


BRANCHES = {
    "KET": {
        "cefr": "A2",
        "color": "#5AA9F5",
        "foundation": "短句绘本 · 生活主题 · 图片线索",
        "challenge": "基础阅读理解 · 简单句型 · 词义匹配",
        "output": "能读懂日常主题小故事，并回答事实性问题。",
    },
    "PET": {
        "cefr": "B1",
        "color": "#26B99A",
        "foundation": "段落阅读 · 细节定位 · 词汇推断",
        "challenge": "观点表达 · 比较对照 · 句型改写",
        "output": "能理解较完整的主题文章，并表达简单观点。",
    },
    "FCE": {
        "cefr": "B2",
        "color": "#F0A14A",
        "foundation": "多文体阅读 · 推断题 · 词汇策略",
        "challenge": "评价观点 · 论证表达 · 写作输出",
        "output": "能分析文章结构、推断隐含信息，并形成书面表达。",
    },
}

SIX_BRANCHES = [
    {
        "name": "KET Foundation",
        "level": "KET · A2",
        "color": "#5AA9F5",
        "goal": "短句绘本、生活主题、图片线索",
        "tasks": "词义匹配 / True-False / 基础细节题",
    },
    {
        "name": "KET Challenge",
        "level": "KET · A2+",
        "color": "#5AA9F5",
        "goal": "稍长故事、基础阅读理解、简单句型",
        "tasks": "选词填空 / 主旨判断 / 简单句合并",
    },
    {
        "name": "PET Foundation",
        "level": "PET · B1",
        "color": "#26B99A",
        "goal": "段落阅读、细节定位、词汇推断",
        "tasks": "阅读选择题 / 词义推断 / 信息定位",
    },
    {
        "name": "PET Challenge",
        "level": "PET · B1+",
        "color": "#26B99A",
        "goal": "观点表达、比较对照、句型改写",
        "tasks": "句型转换 / 开放观点 / 对比理解",
    },
    {
        "name": "FCE Foundation",
        "level": "FCE · B2",
        "color": "#F0A14A",
        "goal": "多文体阅读、推断题、词汇策略",
        "tasks": "推断理解 / 词汇策略 / 段落结构",
    },
    {
        "name": "FCE Challenge",
        "level": "FCE · B2+",
        "color": "#F0A14A",
        "goal": "评价观点、论证表达、写作输出",
        "tasks": "观点评价 / 写作输出 / 高阶复盘",
    },
]


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ink:#14243d;
          --muted:#6e8195;
          --line:#e6edf4;
          --blue:#5aa9f5;
          --mint:#7bd9c5;
          --cream:#fff7e6;
          --coral:#ff6f61;
          --paper:#fffdf8;
        }
        .stApp {
          background:
            radial-gradient(circle at 4% 6%, rgba(123,217,197,.26), transparent 32%),
            radial-gradient(circle at 92% 4%, rgba(255,217,133,.25), transparent 30%),
            linear-gradient(180deg, #f6fbff 0%, #fffdf8 100%);
        }
        div[data-testid="stHeader"] { background: rgba(246,251,255,.72); backdrop-filter: blur(12px); }
        .block-container { padding-top: 2rem; max-width: 1180px; }
        h1, h2, h3 { color: var(--ink); letter-spacing: -0.03em; }
        .hero {
          padding: 34px 36px;
          border: 1px solid rgba(255,255,255,.9);
          border-radius: 30px;
          background: linear-gradient(135deg, rgba(255,255,255,.94), rgba(239,248,255,.9));
          box-shadow: 0 28px 70px -44px rgba(31,92,148,.55);
          margin-bottom: 24px;
        }
        .eyebrow {
          display:inline-flex; padding:7px 13px; border-radius:999px;
          background:#e6f4ff; color:#1774bc; font-size:13px; font-weight:800;
        }
        .hero h1 { font-size: clamp(38px, 5vw, 66px); line-height:1.03; margin: 16px 0 14px; }
        .hero p { color: var(--muted); font-size: 17px; line-height: 1.8; max-width: 820px; }
        .path {
          display:grid; grid-template-columns: 1fr auto 1fr auto 1fr; gap:14px; align-items:center;
          margin: 18px 0 24px;
        }
        .path-card, .branch-card, .report-card, .pullout, .story-panel, .task-card {
          border:1px solid var(--line); border-radius:24px; background:rgba(255,255,255,.88);
          box-shadow: 0 18px 46px -34px rgba(31,92,148,.5);
        }
        .path-card { padding:18px; min-height:128px; }
        .path-card b { font-size:28px; display:block; margin-bottom:4px; }
        .path-card span { color:var(--muted); font-weight:700; }
        .path-card small { display:block; color:var(--muted); line-height:1.6; margin-top:10px; }
        .arrow { color:#9ab0c2; font-size:28px; font-weight:900; }
        .branch-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin: 14px 0 8px; }
        .branch-card { padding:18px; }
        .branch-card h3 { margin:0 0 10px; }
        .branch-card p { color:var(--muted); line-height:1.7; margin:.35rem 0; }
        .pill {
          display:inline-flex; padding:6px 11px; border-radius:999px; margin:4px 5px 4px 0;
          background:#eef7ff; color:#176ba8; font-size:12px; font-weight:800;
        }
        .form-card { padding: 22px; border-radius: 26px; background: rgba(255,255,255,.82); border:1px solid var(--line); }
        .story-panel { padding: 24px; }
        .story-title { font-size: 34px; font-weight: 900; color: var(--ink); line-height:1.1; margin-bottom:8px; }
        .story-meta { color: var(--muted); font-weight:700; margin-bottom:18px; }
        .story-text {
          font-size: 20px; line-height: 2.05; color: #20334d;
          background: linear-gradient(180deg, #ffffff, #fffdf8);
          border: 1px solid var(--line); border-radius: 24px; padding: 24px;
        }
        .highlight {
          background: linear-gradient(transparent 54%, rgba(255,217,133,.9) 0);
          color:#0b73bd; font-weight:900; padding:0 3px; border-radius:5px;
        }
        .word-chip {
          display:inline-flex; padding:8px 13px; margin:5px; border-radius:999px;
          background:#e9f6ff; color:#176ba8; border:1px solid #d6ecfb; font-weight:800;
        }
        .pullout { padding:18px 20px; border-left: 6px solid var(--blue); }
        .pullout b { display:block; color:var(--ink); margin-bottom:6px; }
        .pullout span { color:var(--muted); line-height:1.7; }
        .task-card { padding:18px 20px; margin: 14px 0 8px; border-left: 6px solid var(--mint); }
        .task-card h3 { margin:0 0 6px; }
        .task-card p { color:var(--muted); line-height:1.65; margin:0; }
        .report-card { padding:22px; text-align:center; }
        .report-card strong { font-size:38px; color:var(--blue); display:block; }
        .report-card span { color:var(--muted); font-weight:700; }
        .next-step {
          padding:18px 20px; border-radius:24px; background:linear-gradient(135deg,#eaf7ff,#fff6de);
          border:1px solid var(--line); color:var(--ink); font-weight:800;
        }
        div.stButton > button {
          border-radius: 16px; padding: .72rem 1.2rem; font-weight: 900;
          background: linear-gradient(135deg, #ff6f61, #ff9a64); border: 0;
        }
        @media (max-width: 900px) {
          .path, .branch-grid { grid-template-columns: 1fr; }
          .arrow { display:none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
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
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("selected_branch", SIX_BRANCHES[0]["name"])


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


def get_branch(name: str) -> dict:
    return next(branch for branch in SIX_BRANCHES if branch["name"] == name)


def branch_to_level(branch_name: str) -> str:
    return branch_name.split(" ", 1)[0]


def highlight_words(text: str, words: list[str]) -> str:
    output = text
    for word in sorted(words, key=len, reverse=True):
        output = output.replace(word, f"<span class='highlight'>{word}</span>")
    return output


def render_path() -> None:
    st.caption("点击任一节点，会自动切换到对应学习分支。")
    for start in range(0, len(SIX_BRANCHES), 3):
        cols = st.columns(3, gap="medium")
        for col, branch in zip(cols, SIX_BRANCHES[start : start + 3]):
            with col:
                if st.button(
                    f"{branch['name']}\n\n{branch['level']}",
                    key=f"path-{branch['name']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_branch = branch["name"]
                    st.rerun()


def render_branches() -> None:
    branch = get_branch(st.session_state.selected_branch)
    with st.container(border=True):
        st.markdown(f"### 当前分支：{branch['name']}")
        st.caption(branch["level"])
        col1, col2 = st.columns(2)
        col1.markdown(f"**目标能力**  \n{branch['goal']}")
        col2.markdown(f"**练习任务**  \n{branch['tasks']}")


def render_reference_table() -> None:
    st.markdown("#### 简化分级对照")
    rows = [
        ("KET Foundation", "A2", "短句绘本", "词义匹配 / 判断 / 细节题"),
        ("KET Challenge", "A2+", "稍长故事", "选词填空 / 主旨判断 / 简单句型"),
        ("PET Foundation", "B1", "段落阅读", "细节定位 / 词汇推断 / 信息定位"),
        ("PET Challenge", "B1+", "观点阅读", "句型改写 / 比较对照 / 开放观点"),
        ("FCE Foundation", "B2", "多文体阅读", "推断理解 / 词汇策略 / 段落结构"),
        ("FCE Challenge", "B2+", "高阶输出", "评价观点 / 写作输出 / 综合复盘"),
    ]
    st.dataframe(
        [
            {"学习分支": branch, "对应级别": cefr, "阅读形态": reading, "核心练习": tasks}
            for branch, cefr, reading, tasks in rows
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_home() -> None:
    st.markdown(
        """
        <div class="hero">
          <span class="eyebrow">AI graded reader studio</span>
          <h1>分级英语词汇绘本阅读与练习系统</h1>
          <p>从 KET 到 FCE，围绕目标词汇自动生成英文绘本/阅读文章、真实 AI 插图、专属 Worksheet 和学习复盘报告。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 生成工作台")
    st.caption("先选学习分支，再生成当前分支对应难度的阅读、插图和 Worksheet。")
    with st.container(border=True):
        col1, col2, col3 = st.columns([1.25, 1, 1.2])
        with col1:
            branch_options = [branch["name"] for branch in SIX_BRANCHES]
            branch_name = st.selectbox(
                "学习分支",
                branch_options,
                index=branch_options.index(st.session_state.selected_branch),
            )
            st.session_state.selected_branch = branch_name
            level = branch_to_level(branch_name)
        with col2:
            mode_label = st.selectbox("内容模式", ["绘本故事模式", "标准阅读文章模式"])
            mode = "picture" if mode_label == "绘本故事模式" else "reading"
        with col3:
            theme = st.text_input("主题（可选）", placeholder="如 School life / Animal helpers")

        st.info("选择等级与模式后，系统会同时生成阅读内容、目标词汇高亮、真实绘本插图和随文练习。")
        if st.button("一键生成素材", type="primary"):
            with st.spinner("正在生成阅读、练习和真实配图，生图可能需要 30-90 秒..."):
                st.session_state.reading = generate_reading(level, mode, theme.strip() or None)
                st.session_state.result = None
            st.rerun()

    render_branches()

    st.markdown("### 学习地图")
    st.caption("这部分放在页面底部作为辅助导航，不打断主要生成流程。")
    with st.expander("展开学习路径：KET Foundation → FCE Challenge", expanded=False):
        render_path()

    with st.expander("展开分级对照表（参考资料）", expanded=False):
        render_reference_table()


def render_reading() -> None:
    reading = st.session_state.reading
    if not reading:
        st.info("请先在首页生成一篇阅读。")
        return

    bridge = reading["bridge"]
    st.markdown(
        f"""
        <div class="story-panel">
          <div class="story-title">{reading['title']}</div>
          <div class="story-meta">{reading['level']} {bridge['cefr']} · {bridge['stage']} · {bridge['lesson_idea']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    image_col, text_col = st.columns([1.06, 0.94], gap="large")
    with image_col:
        if reading["image_url"]:
            st.image(reading["image_url"], use_container_width=True)
        else:
            st.warning(f"图片暂未生成：{reading['image_status']}")
        with st.expander("配图 Prompt"):
            st.write(reading["illustration_prompt"])

    with text_col:
        st.markdown("#### Story Reader")
        story_html = "".join(
            f"<p>{highlight_words(paragraph, reading['target_words'])}</p>" for paragraph in reading["paragraphs"]
        )
        st.markdown(f"<div class='story-text'>{story_html}</div>", unsafe_allow_html=True)

    st.markdown("### 本篇核心词汇")
    chips = "".join(f"<span class='word-chip'>{word}</span>" for word in reading["target_words"])
    st.markdown(chips, unsafe_allow_html=True)


def render_exercises() -> None:
    reading = st.session_state.reading
    if not reading:
        st.info("请先生成阅读。")
        return

    st.markdown("## Worksheet 任务卡")
    answers = {}
    for index, ex in enumerate(reading["exercises"], start=1):
        st.markdown(
            f"""
            <div class="task-card">
              <h3>{index}. {ex['title']}</h3>
              <p>{ex['prompt']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if ex["type"] == "matching":
            answers[ex["id"]] = {}
            meanings = [item["meaning"] for item in ex["items"]]
            cols = st.columns(2)
            for item_index, item in enumerate(ex["items"]):
                with cols[item_index % 2]:
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
            answers[ex["id"]] = st.text_input("请输入完整句子", key=ex["id"])

    if st.button("提交批改", type="primary"):
        st.session_state.result = grade(reading, answers)
        st.rerun()


def render_result() -> None:
    result = st.session_state.result
    if not result:
        st.info("完成练习并提交后，这里会显示结果。")
        return

    st.markdown("## 学习报告")
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='report-card'><strong>{result['percent']}%</strong><span>正确率</span></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='report-card'><strong>{result['score']}/{result['total']}</strong><span>得分</span></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='report-card'><strong>{result['rating']}</strong><span>评级</span></div>", unsafe_allow_html=True)

    st.markdown("### 薄弱词汇")
    st.markdown("".join(f"<span class='word-chip'>{word}</span>" for word in result["weakWords"]), unsafe_allow_html=True)
    st.markdown("<div class='next-step'>下一步建议：先复习薄弱词汇，再重新完成本篇 Worksheet；如果正确率超过 80%，可以切换到 Challenge 分支。</div>", unsafe_allow_html=True)

    st.markdown("### 错题复盘")
    for item in result["details"]:
        with st.expander(f"{'正确' if item['correct'] else '需要复习'} · {item['title']}", expanded=not item["correct"]):
            st.write("你的答案：", item["yourAnswer"])
            st.write("正确答案：", item["answer"])
            st.write(item["explanation"])


inject_css()
load_streamlit_secrets()
init_state()

tabs = st.tabs(["首页", "阅读", "练习", "结果"])
with tabs[0]:
    render_home()
with tabs[1]:
    render_reading()
with tabs[2]:
    render_exercises()
with tabs[3]:
    render_result()
