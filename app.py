from __future__ import annotations

import random
import re
import base64
import json
import os
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from urllib import error, request
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


ExamLevel = Literal["KET", "PET", "FCE"]
Mode = Literal["picture", "reading"]


app = FastAPI(title="KET/PET/FCE Vocabulary Reading Lab")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

GENERATED_DIR = Path("static/generated")
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def load_local_env() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.lstrip("\ufeff").split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


VOCAB: dict[ExamLevel, list[dict[str, str]]] = {
    "KET": [
        {"word": "adventure", "meaning": "an exciting trip or experience"},
        {"word": "brave", "meaning": "not afraid"},
        {"word": "careful", "meaning": "doing something with attention"},
        {"word": "village", "meaning": "a small town in the country"},
        {"word": "journey", "meaning": "travel from one place to another"},
        {"word": "forest", "meaning": "a place with many trees"},
        {"word": "weather", "meaning": "sun, rain, wind, or snow"},
        {"word": "friendly", "meaning": "kind and nice to others"},
        {"word": "healthy", "meaning": "strong and not ill"},
        {"word": "borrow", "meaning": "to take and return later"},
        {"word": "decide", "meaning": "to choose what to do"},
        {"word": "practice", "meaning": "to do something again to improve"},
    ],
    "PET": [
        {"word": "environment", "meaning": "the natural world around us"},
        {"word": "improve", "meaning": "to make something better"},
        {"word": "confident", "meaning": "sure about your ability"},
        {"word": "compare", "meaning": "to look for similarities and differences"},
        {"word": "community", "meaning": "people living or working together"},
        {"word": "solution", "meaning": "an answer to a problem"},
        {"word": "encourage", "meaning": "to give someone confidence"},
        {"word": "describe", "meaning": "to say what something is like"},
        {"word": "reduce", "meaning": "to make smaller or less"},
        {"word": "responsible", "meaning": "able to be trusted"},
        {"word": "opinion", "meaning": "what someone thinks"},
        {"word": "discover", "meaning": "to find something new"},
    ],
    "FCE": [
        {"word": "sustainable", "meaning": "able to continue without harming the future"},
        {"word": "perspective", "meaning": "a way of thinking about something"},
        {"word": "significant", "meaning": "important or large enough to notice"},
        {"word": "consequence", "meaning": "a result of an action"},
        {"word": "innovative", "meaning": "using new ideas or methods"},
        {"word": "resilient", "meaning": "able to recover after difficulty"},
        {"word": "evaluate", "meaning": "to judge the value or quality of something"},
        {"word": "interpret", "meaning": "to explain the meaning of something"},
        {"word": "evidence", "meaning": "facts that support an idea"},
        {"word": "phenomenon", "meaning": "an event or fact that can be studied"},
        {"word": "collaborate", "meaning": "to work with others"},
        {"word": "adaptation", "meaning": "a change that helps survival or success"},
    ],
}


LEVEL_BRIDGE = {
    "KET": {
        "cefr": "A2",
        "stage": "Foundation / Challenge",
        "lesson_idea": "生活主题、短句绘本、图片线索、基础理解与词义匹配",
        "themes": ["My neighborhood", "Animal friends", "Weather and seasons", "School life"],
    },
    "PET": {
        "cefr": "B1",
        "stage": "Foundation / Challenge",
        "lesson_idea": "段落阅读、细节定位、观点表达、比较对照与句型改写",
        "themes": ["Our Earth", "Healthy choices", "Animal helpers", "Discovering mysteries"],
    },
    "FCE": {
        "cefr": "B2",
        "stage": "Foundation / Challenge",
        "lesson_idea": "多文体阅读、推断评价、词汇策略、论证表达与写作输出",
        "themes": ["Meet the challenge", "Wild encounters", "The power of storytelling", "Change it up"],
    },
}


SESSIONS: dict[str, dict[str, Any]] = {}
HISTORY: list[dict[str, Any]] = []


class GenerateRequest(BaseModel):
    level: ExamLevel
    mode: Mode
    theme: str | None = Field(default=None, max_length=80)


class SubmitRequest(BaseModel):
    reading_id: str
    answers: dict[str, Any]


def select_words(level: ExamLevel, count: int) -> list[dict[str, str]]:
    return random.sample(VOCAB[level], min(count, len(VOCAB[level])))


def make_title(level: ExamLevel, mode: Mode, theme: str) -> str:
    if mode == "picture":
        return f"{theme}: A {level} Picture Story"
    return f"{theme}: A {level} Reading Passage"


def make_text(level: ExamLevel, mode: Mode, words: list[dict[str, str]], theme: str) -> list[str]:
    by_word = {item["word"]: item["word"] for item in words}

    def w(name: str) -> str:
        return by_word.get(name, name)

    if mode == "picture":
        if level == "KET":
            return [
                f"Mia lives in a small {w('village')} near a green {w('forest')}. One morning, her class starts a short {w('journey')} for a little {w('adventure')}.",
                f"Mia wants to be {w('brave')}, but she is also {w('careful')}. She checks the {w('weather')} and asks to {w('borrow')} a map from her teacher.",
                f"On the path, a {w('friendly')} dog walks with the children. They stop for a {w('healthy')} snack and {w('practice')} new English words.",
                f"When clouds come, Mia must {w('decide')} what to do. She says, \"Let's go back together,\" and everyone gets home safely.",
            ]
        if level == "PET":
            return [
                f"In a small {w('community')}, Leo and his friends want to {w('improve')} a garden for children and birds.",
                f"They {w('compare')} two plans and {w('describe')} each idea with pictures. Their teacher asks for one clear {w('opinion')}.",
                f"Leo feels more {w('confident')} when his friends {w('encourage')} him. Together, they find a simple {w('solution')} to {w('reduce')} waste.",
                f"The project helps them become {w('responsible')} learners who care about the {w('environment')} and love to {w('discover')} new things.",
            ]
        return [
            f"Nova visits a science fair where students show an {w('innovative')} model of a {w('sustainable')} city.",
            f"She listens from a new {w('perspective')} and looks for {w('evidence')} before she gives her answer.",
            f"One display explains a natural {w('phenomenon')}; another shows how animal {w('adaptation')} can be {w('significant')}.",
            f"Nova learns to {w('evaluate')} ideas, {w('interpret')} data, and {w('collaborate')} with a {w('resilient')} team.",
        ]

    if level == "KET":
        return [
            f"Last Saturday, a class planned a short {w('journey')} from their {w('village')} to a nearby {w('forest')}. The teacher asked everyone to be {w('careful')} and to check the {w('weather')}.",
            f"During the walk, the children saw animals, drew pictures, and wrote new words in their notebooks. A {w('friendly')} classmate helped Ben {w('borrow')} a pencil.",
            f"The trip became a small {w('adventure')}. The children learned to be {w('brave')}, make {w('healthy')} choices, {w('practice')} English, and {w('decide')} as a team.",
        ]
    if level == "PET":
        return [
            f"A local school wanted to {w('improve')} its playground and make the area better for the {w('environment')}. Students worked with the {w('community')} to design a realistic plan.",
            f"First, they had to {w('compare')} two ideas: planting trees or building a small reading corner. Each group had to {w('describe')} its plan and explain its {w('opinion')}.",
            f"In the end, they chose a mixed {w('solution')} that could {w('reduce')} waste and create shade. The project helped students become more {w('confident')} and {w('responsible')}.",
            f"Most importantly, the teacher tried to {w('encourage')} every learner to {w('discover')} how small actions can change a shared space.",
        ]
    return [
        f"In many schools, environmental education has become a {w('significant')} part of the curriculum. Students are encouraged to examine each local {w('phenomenon')} from more than one {w('perspective')}.",
        f"One class studied animal {w('adaptation')} and collected {w('evidence')} from photographs, maps, and short articles. Their task was to {w('evaluate')} whether human activity had changed the habitat.",
        f"The project had an important {w('consequence')}: learners did not simply memorize facts. They learned to {w('interpret')} information, {w('collaborate')} with classmates, and propose {w('innovative')} but realistic solutions.",
        f"Such work can make young people more {w('resilient')} when they face complex problems, especially if the final plan is practical and {w('sustainable')}.",
    ]


def sentence_pool(level: ExamLevel) -> dict[str, str]:
    if level == "KET":
        return {
            "prompt": "Rewrite: Mia is brave. Mia is careful.",
            "answer": "Mia is brave and careful.",
            "hint": "Use 'and' to join two simple ideas.",
        }
    if level == "PET":
        return {
            "prompt": "Rewrite using 'because': The students chose trees. Trees help the environment.",
            "answer": "The students chose trees because they help the environment.",
            "hint": "Join reason and action with because.",
        }
    return {
        "prompt": "Rewrite using 'not only ... but also': The project improved reading. It improved critical thinking.",
        "answer": "The project not only improved reading but also improved critical thinking.",
        "hint": "Use the paired structure to show two benefits.",
    }


def build_exercises(level: ExamLevel, mode: Mode, text: list[str], words: list[dict[str, str]]) -> list[dict[str, Any]]:
    flat_text = " ".join(text)
    match_items = words[:4]
    cloze_word = words[4]["word"] if len(words) > 4 else words[0]["word"]
    cloze_sentence = re.sub(rf"\b{re.escape(cloze_word)}\b", "_____", flat_text, count=1, flags=re.I)
    transform = sentence_pool(level)

    exercises: list[dict[str, Any]] = [
        {
            "id": "q1",
            "type": "matching",
            "title": "Word Meaning Match",
            "prompt": "Match each target word with its meaning.",
            "items": [{"word": i["word"], "meaning": i["meaning"]} for i in match_items],
            "answer": {i["word"]: i["meaning"] for i in match_items},
        },
        {
            "id": "q2",
            "type": "cloze",
            "title": "Choose the Missing Word",
            "prompt": cloze_sentence,
            "options": random.sample([i["word"] for i in words], min(5, len(words))),
            "answer": cloze_word,
        },
        {
            "id": "q3",
            "type": "mcq",
            "title": "Reading Comprehension",
            "prompt": "What is the main purpose of the reading?",
            "options": [
                "To describe a learning experience connected to the theme",
                "To list unrelated vocabulary only",
                "To explain a grammar rule without a story",
                "To give travel prices",
            ],
            "answer": "To describe a learning experience connected to the theme",
            "explanation": "The passage uses target words inside a complete theme-based reading task.",
        },
        {
            "id": "q4",
            "type": "true_false",
            "title": "True or False",
            "prompt": "The reading includes several highlighted target vocabulary words.",
            "answer": True,
            "explanation": "The generation engine embeds and highlights words from the selected exam level.",
        },
        {
            "id": "q5",
            "type": "transform",
            "title": "Sentence Transformation",
            "prompt": transform["prompt"],
            "answer": transform["answer"],
            "hint": transform["hint"],
            "enabled": level in {"PET", "FCE"} or mode == "reading",
        },
    ]
    return [e for e in exercises if e.get("enabled", True)]


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower()).rstrip(".")


def grade(session: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
    details = []
    correct = 0
    for ex in session["exercises"]:
        qid = ex["id"]
        expected = ex["answer"]
        given = answers.get(qid)
        is_correct = False
        if ex["type"] == "matching":
            is_correct = isinstance(given, dict) and all(given.get(k) == v for k, v in expected.items())
        elif ex["type"] == "true_false":
            is_correct = given is expected or str(given).lower() == str(expected).lower()
        else:
            is_correct = normalize(given) == normalize(expected)

        correct += int(is_correct)
        details.append(
            {
                "id": qid,
                "title": ex["title"],
                "correct": is_correct,
                "yourAnswer": given,
                "answer": expected,
                "explanation": ex.get("explanation") or ex.get("hint") or "Review the highlighted vocabulary and the sentence context.",
            }
        )
    total = len(session["exercises"])
    percent = round(correct / total * 100)
    rating = "Excellent" if percent >= 90 else "Good" if percent >= 75 else "Keep Practicing" if percent >= 60 else "Needs Review"
    weak_words = session["target_words"][:3] if percent < 80 else session["target_words"][3:6]
    return {
        "score": correct,
        "total": total,
        "percent": percent,
        "rating": rating,
        "details": details,
        "weakWords": weak_words,
    }


def build_illustration_prompt(level: ExamLevel, mode: Mode, theme: str, paragraphs: list[str]) -> str:
    mode_hint = (
        "a warm children's picture book spread for young English learners"
        if mode == "picture"
        else "a polished editorial illustration for an English graded reader"
    )
    level_hint = {
        "KET": "simple, friendly, clear objects, suitable for A2 children",
        "PET": "slightly richer scene, school project feeling, suitable for B1 learners",
        "FCE": "more mature composition, thoughtful academic reading mood, suitable for B2 learners",
    }[level]
    story_hint = " ".join(paragraphs[:2])
    return (
        f"Create {mode_hint}. Theme: {theme}. Exam level: {level}. "
        f"Style: soft blue-white palette, clean modern children's book illustration, gentle light, "
        f"rounded shapes, high-quality composition, no scary elements, no text, no letters, no watermark. "
        f"Difficulty mood: {level_hint}. Scene should visually support this reading: {story_hint}"
    )


def generate_illustration_image(reading_id: str, level: ExamLevel, mode: Mode, theme: str, paragraphs: list[str]) -> dict[str, str | None]:
    api_key = os.getenv("IMAROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    prompt = build_illustration_prompt(level, mode, theme, paragraphs)
    if not api_key:
        return {
            "image_url": None,
            "image_status": "missing_api_key",
            "illustration_prompt": prompt,
        }

    endpoint = os.getenv("IMAGE_API_URL", "https://api.imarouter.com/v1/images/generations")
    model = os.getenv("IMAGE_MODEL", "gpt-image-2")
    payload = {
        "model": model,
        "prompt": prompt,
        "size": os.getenv("IMAGE_SIZE", "1024x1024"),
        "n": 1,
    }

    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        return {"image_url": None, "image_status": f"api_error_{exc.code}: {detail[:240]}", "illustration_prompt": prompt}
    except Exception as exc:
        return {"image_url": None, "image_status": f"api_error: {exc}", "illustration_prompt": prompt}

    task_id = data.get("task_id") or data.get("id")
    if task_id and not data.get("data"):
        polled = poll_image_task(endpoint, task_id, api_key)
        if polled.get("image_url"):
            polled["illustration_prompt"] = prompt
            return polled
        return {
            "image_url": None,
            "image_status": polled.get("image_status") or f"task_pending_or_failed: {task_id}",
            "illustration_prompt": prompt,
        }

    item = (data.get("data") or [{}])[0]
    if item.get("b64_json"):
        image_bytes = base64.b64decode(item["b64_json"])
        out = GENERATED_DIR / f"{reading_id}.png"
        out.write_bytes(image_bytes)
        return {"image_url": f"/static/generated/{reading_id}.png", "image_status": "generated", "illustration_prompt": prompt}
    if item.get("url"):
        return {"image_url": item["url"], "image_status": "generated_url", "illustration_prompt": prompt}
    return {"image_url": None, "image_status": "api_returned_no_image", "illustration_prompt": prompt}


def poll_image_task(endpoint: str, task_id: str, api_key: str) -> dict[str, str | None]:
    status_url = f"{endpoint.rstrip('/')}/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    last_status = "submitted"
    for _ in range(36):
        req = request.Request(status_url, headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return {"image_url": None, "image_status": f"poll_error: {exc}"}

        image_url = extract_image_url(payload)
        status = extract_task_status(payload) or last_status
        last_status = status
        if image_url:
            return {"image_url": image_url, "image_status": status}
        if status in {"failed", "error", "cancelled", "expired"}:
            return {"image_url": None, "image_status": status}
        time.sleep(3)
    return {"image_url": None, "image_status": f"timeout_waiting_for_image: {last_status}"}


def extract_task_status(payload: dict[str, Any]) -> str | None:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    status = data.get("status") if isinstance(data, dict) else None
    if status == "succeeded":
        return "generated"
    if status == "completed":
        return "generated"
    return status


def extract_image_url(payload: dict[str, Any]) -> str | None:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        return None
    if isinstance(data.get("url"), str):
        return data["url"]
    if isinstance(data.get("output"), list) and data["output"]:
        first = data["output"][0]
        if isinstance(first, dict) and isinstance(first.get("url"), str):
            return first["url"]
    if isinstance(data.get("unsigned_urls"), list) and data["unsigned_urls"]:
        return data["unsigned_urls"][0]
    result = data.get("result")
    if isinstance(result, dict):
        images = result.get("images")
        if isinstance(images, list) and images:
            first_image = images[0]
            if isinstance(first_image, dict):
                url = first_image.get("url")
                if isinstance(url, list) and url:
                    return url[0]
                if isinstance(url, str):
                    return url
    return None


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "levels": ["KET", "PET", "FCE"],
        "modes": ["picture", "reading"],
        "bridge": LEVEL_BRIDGE,
    }


@app.post("/api/generate")
def generate(req: GenerateRequest) -> dict[str, Any]:
    bridge = LEVEL_BRIDGE[req.level]
    theme = req.theme or random.choice(bridge["themes"])
    words = select_words(req.level, 12)
    text = make_text(req.level, req.mode, words, theme)
    exercises = build_exercises(req.level, req.mode, text, words)
    reading_id = str(uuid4())
    image = generate_illustration_image(reading_id, req.level, req.mode, theme, text)
    payload = {
        "id": reading_id,
        "level": req.level,
        "mode": req.mode,
        "title": make_title(req.level, req.mode, theme),
        "theme": theme,
        "bridge": bridge,
        "target_words": [w["word"] for w in words],
        "word_bank": words,
        "paragraphs": text,
        "illustration_prompt": image["illustration_prompt"],
        "image_url": image["image_url"],
        "image_status": image["image_status"],
        "exercises": exercises,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    SESSIONS[reading_id] = payload
    HISTORY.insert(0, {k: payload[k] for k in ["id", "level", "mode", "title", "created_at"]})
    response_payload = deepcopy(payload)
    for item in response_payload["exercises"]:
        item.pop("answer", None)
    return response_payload


@app.post("/api/submit")
def submit(req: SubmitRequest) -> dict[str, Any]:
    session = SESSIONS.get(req.reading_id)
    if not session:
        raise HTTPException(status_code=404, detail="Reading session not found")
    result = grade(session, req.answers)
    session["last_result"] = result
    return result


@app.get("/api/history")
def history() -> dict[str, Any]:
    return {"items": HISTORY[:20]}
