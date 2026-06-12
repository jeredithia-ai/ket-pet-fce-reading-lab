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


st.set_page_config(page_title="AI Graded Reading Lab", page_icon="📘", layout="wide")


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

STAGES = [
    {
        "id": "stage-1",
        "stage": "Stage 1",
        "name": "Picture Starter",
        "age": "6-8",
        "cefr": "Pre-A1 / A1-",
        "exam": "YLE Starters bridge",
        "generator_level": "KET",
        "color": "#77C8F2",
        "height": 84,
        "ability": "看图识词，读懂颜色、地点、人物和动作类短句。",
        "tasks": "图片线索 / 词义匹配 / True-False",
        "reader": "一句一图，重复句型，降低第一次阅读压力。",
        "next": "能稳定读懂短句后，进入 KET Starter。",
    },
    {
        "id": "stage-2",
        "stage": "Stage 2",
        "name": "KET Starter",
        "age": "7-10",
        "cefr": "A1 / A2-",
        "exam": "YLE Movers to KET",
        "generator_level": "KET",
        "color": "#5AA9F5",
        "height": 106,
        "ability": "读懂生活主题小故事，抓住 who / where / what 等事实信息。",
        "tasks": "词义匹配 / 基础细节题 / 简单选择题",
        "reader": "短句绘本，主题贴近日常生活和学校场景。",
        "next": "能完成基础细节题后，进入 KET Reader。",
    },
    {
        "id": "stage-3",
        "stage": "Stage 3",
        "name": "KET Reader",
        "age": "8-11",
        "cefr": "A2- / A2",
        "exam": "A2 Key foundation",
        "generator_level": "KET",
        "color": "#7BD9C5",
        "height": 128,
        "ability": "读完整故事，理解事件顺序、人物目标和基础原因。",
        "tasks": "选词填空 / 主旨判断 / 句子排序",
        "reader": "稍长故事，开始训练段落衔接和故事结构。",
        "next": "能复述故事主线后，进入 PET Builder。",
    },
    {
        "id": "stage-4",
        "stage": "Stage 4",
        "name": "PET Builder",
        "age": "10-13",
        "cefr": "A2+ / B1-",
        "exam": "B1 Preliminary bridge",
        "generator_level": "PET",
        "color": "#26B99A",
        "height": 150,
        "ability": "阅读段落文章，定位细节，并根据上下文推断词义。",
        "tasks": "信息定位 / 词义推断 / 多选理解",
        "reader": "从故事过渡到文章，加入观点、比较和解释。",
        "next": "能解释答案依据后，进入 PET Thinker。",
    },
    {
        "id": "stage-5",
        "stage": "Stage 5",
        "name": "PET Thinker",
        "age": "11-14",
        "cefr": "B1 / B1+",
        "exam": "B1 Preliminary",
        "generator_level": "PET",
        "color": "#F4C15D",
        "height": 172,
        "ability": "理解观点、原因和比较关系，开始形成简短书面表达。",
        "tasks": "句型转换 / 开放观点 / 对比理解",
        "reader": "主题文章与故事并行，强调观点表达和句型迁移。",
        "next": "能完成观点表达后，进入 FCE Explorer。",
    },
    {
        "id": "stage-6",
        "stage": "Stage 6",
        "name": "FCE Explorer",
        "age": "13+",
        "cefr": "B2-",
        "exam": "B2 First foundation",
        "generator_level": "FCE",
        "color": "#FF8A65",
        "height": 194,
        "ability": "阅读更长文本，推断隐含信息，分析文章结构和作者意图。",
        "tasks": "高阶 cloze / 推断理解 / 写作输出",
        "reader": "多文体阅读，加入论证、评价和复盘输出。",
        "next": "适合继续扩展到完整 FCE / B2 备考。",
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
        .stage-tower {
          min-height: 258px; display:flex; flex-direction:column; justify-content:flex-end;
          padding: 12px 10px; border-radius: 24px; border:1px solid var(--line);
          background: rgba(255,255,255,.72); box-shadow: 0 16px 42px -36px rgba(31,92,148,.5);
        }
        .stage-tower.current { outline: 3px solid rgba(255,111,97,.28); background: rgba(255,255,255,.96); }
        .stage-bar {
          border-radius: 18px 18px 10px 10px; display:flex; flex-direction:column; justify-content:flex-end;
          padding: 12px 10px; color:#fff; text-shadow: 0 1px 10px rgba(23,42,64,.26);
        }
        .stage-bar b { font-size: 17px; line-height:1.15; }
        .stage-bar span { font-size: 12px; font-weight:800; opacity:.94; margin-top:4px; }
        .stage-foot { padding-top:10px; min-height:70px; }
        .stage-foot strong { color:var(--ink); font-size:14px; display:block; }
        .stage-foot small { color:var(--muted); font-weight:800; }
        .stage-summary {
          margin: 18px 0 22px; padding: 22px; border-radius: 26px;
          border:1px solid var(--line); background:linear-gradient(135deg, rgba(255,255,255,.94), rgba(255,247,230,.86));
          box-shadow: 0 18px 46px -36px rgba(31,92,148,.5);
        }
        .stage-summary h3 { margin:0 0 8px; }
        .stage-summary p { color:var(--muted); line-height:1.75; margin:.35rem 0; }
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
    st.session_state.setdefault("selected_stage", STAGES[0]["id"])


def generate_reading(level: str, mode: str, theme: str | None, stage: dict | None = None) -> dict:
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
        "stage_profile": stage,
    }


def get_stage(stage_id: str) -> dict:
    return next(stage for stage in STAGES if stage["id"] == stage_id)


def stage_label(stage: dict) -> str:
    return f"{stage['stage']} · {stage['name']} · {stage['cefr']}"


def highlight_words(text: str, words: list[str]) -> str:
    output = text
    for word in sorted(words, key=len, reverse=True):
        output = output.replace(word, f"<span class='highlight'>{word}</span>")
    return output


def render_path() -> None:
    st.caption("点击任一节点，会自动切换到对应学习阶段。")
    for start in range(0, len(STAGES), 3):
        cols = st.columns(3, gap="medium")
        for col, stage in zip(cols, STAGES[start : start + 3]):
            with col:
                if st.button(
                    f"{stage['stage']} · {stage['name']}\n\n{stage['cefr']} · Age {stage['age']}",
                    key=f"path-{stage['id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_stage = stage["id"]
                    st.rerun()


def render_stage_pillars() -> None:
    cols = st.columns(6, gap="small")
    for col, stage in zip(cols, STAGES):
        current = stage["id"] == st.session_state.selected_stage
        class_name = "stage-tower current" if current else "stage-tower"
        with col:
            st.markdown(
                f"""
                <div class="{class_name}">
                  <div class="stage-bar" style="height:{stage['height']}px;background:linear-gradient(180deg,{stage['color']},#ff8a65);">
                    <b>{stage['stage']}</b>
                    <span>{stage['cefr']}</span>
                  </div>
                  <div class="stage-foot">
                    <strong>{stage['name']}</strong>
                    <small>Age {stage['age']}</small>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("选择", key=f"stage-{stage['id']}", use_container_width=True):
                st.session_state.selected_stage = stage["id"]
                st.rerun()


def render_stage_summary() -> None:
    stage = get_stage(st.session_state.selected_stage)
    st.markdown(
        f"""
        <div class="stage-summary">
          <span class="eyebrow">{stage['exam']} · Age {stage['age']}</span>
          <h3>{stage['stage']} · {stage['name']}</h3>
          <p><b>能力目标：</b>{stage['ability']}</p>
          <p><b>阅读形态：</b>{stage['reader']}</p>
          <p><b>练习重点：</b>{stage['tasks']}</p>
          <p><b>下一步：</b>{stage['next']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_reference_table() -> None:
    st.markdown("#### 六阶段 / CEFR / 考级桥接对照")
    st.dataframe(
        [
            {
                "阶段": f"{stage['stage']} · {stage['name']}",
                "年龄": stage["age"],
                "CEFR": stage["cefr"],
                "考试桥接": stage["exam"],
                "系统生成等级": stage["generator_level"],
                "核心练习": stage["tasks"],
            }
            for stage in STAGES
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_home() -> None:
    st.markdown(
        """
        <div class="hero">
          <span class="eyebrow">AI graded reader studio</span>
          <h1>六阶段英语阅读成长地图</h1>
          <p>从 Pre-A1 图像阅读到 FCE 入门，用能力阶段引导学生一步步生成故事、完成练习，并获得可复盘的学习报告。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 选择学习阶段")
    st.caption("六根能力柱代表孩子从看图读短句到高阶文章理解的成长路线。")
    render_stage_pillars()
    render_stage_summary()

    st.markdown("### 生成工作台")
    st.caption("确认阶段后，再生成当前阶段对应难度的阅读、插图和 Worksheet。")
    with st.container(border=True):
        col1, col2, col3 = st.columns([1.25, 1, 1.2])
        with col1:
            stage_options = [stage_label(stage) for stage in STAGES]
            selected_stage = get_stage(st.session_state.selected_stage)
            stage_choice = st.selectbox(
                "学习阶段",
                stage_options,
                index=STAGES.index(selected_stage),
            )
            selected_index = stage_options.index(stage_choice)
            st.session_state.selected_stage = STAGES[selected_index]["id"]
            selected_stage = STAGES[selected_index]
            level = selected_stage["generator_level"]
        with col2:
            mode_label = st.selectbox("内容模式", ["绘本故事模式", "标准阅读文章模式"])
            mode = "picture" if mode_label == "绘本故事模式" else "reading"
        with col3:
            theme = st.text_input("主题（可选）", placeholder="如 School life / Animal helpers")

        st.info(
            f"当前阶段会使用 {selected_stage['generator_level']} 词汇池生成内容；"
            f"目标能力是：{selected_stage['ability']}"
        )
        if st.button("一键生成素材", type="primary"):
            with st.spinner("正在生成阅读、练习和真实配图，生图可能需要 30-90 秒..."):
                st.session_state.reading = generate_reading(level, mode, theme.strip() or None, selected_stage)
                st.session_state.result = None
            st.rerun()

    st.markdown("### 学习地图")
    st.caption("这部分放在页面底部作为辅助导航，不打断主要生成流程。")
    with st.expander("展开六阶段路径", expanded=False):
        render_path()

    with st.expander("展开分级对照表（参考资料）", expanded=False):
        render_reference_table()


def render_reading() -> None:
    reading = st.session_state.reading
    if not reading:
        st.info("请先在首页生成一篇阅读。")
        return

    bridge = reading["bridge"]
    stage = reading.get("stage_profile")
    stage_meta = (
        f"{stage['stage']} · {stage['name']} · {stage['cefr']}"
        if stage
        else f"{reading['level']} {bridge['cefr']}"
    )
    st.markdown(
        f"""
        <div class="story-panel">
          <div class="story-title">{reading['title']}</div>
          <div class="story-meta">{stage_meta} · {bridge['lesson_idea']}</div>
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
        st.markdown("#### 分级阅读")
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

    stage = reading.get("stage_profile")
    if stage:
        st.caption(f"{stage['stage']} · {stage['name']} 练习重点：{stage['tasks']}")
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
    reading = st.session_state.reading
    stage = reading.get("stage_profile") if reading else None
    next_step = stage["next"] if stage else "如果正确率超过 80%，可以挑战下一阶段。"
    st.markdown(
        f"<div class='next-step'>下一步建议：先复习薄弱词汇，再重新完成本篇 Worksheet；{next_step}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### 错题复盘")
    for item in result["details"]:
        with st.expander(f"{'正确' if item['correct'] else '需要复习'} · {item['title']}", expanded=not item["correct"]):
            st.write("你的答案：", item["yourAnswer"])
            st.write("正确答案：", item["answer"])
            st.write(item["explanation"])


inject_css()
load_streamlit_secrets()
init_state()

tabs = st.tabs(["阶段生成", "阅读故事", "练习任务", "学习报告"])
with tabs[0]:
    render_home()
with tabs[1]:
    render_reading()
with tabs[2]:
    render_exercises()
with tabs[3]:
    render_result()
