let currentReading = null
let currentResult = null

const $ = (id) => document.getElementById(id)

function showPage(id) {
  if ((id === 'reading' || id === 'exercise') && !currentReading) {
    showPage('home')
    return
  }
  if (id === 'result' && !currentResult) {
    showPage(currentReading ? 'exercise' : 'home')
    return
  }
  document.querySelectorAll('.page').forEach((page) => page.classList.toggle('active', page.id === id))
  document.querySelectorAll('.nav-btn').forEach((btn) => btn.classList.toggle('active', btn.dataset.jump === id))
}

function unlockNav(...ids) {
  ids.forEach((id) => {
    document.querySelector(`.nav-btn[data-jump="${id}"]`)?.classList.remove('locked')
  })
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlight(text, words) {
  let output = text
  words.forEach((word) => {
    output = output.replace(new RegExp(`\\b(${escapeRegExp(word)})\\b`, 'gi'), '<span class="target">$1</span>')
  })
  return output
}

function levelName(mode) {
  return mode === 'picture' ? '绘本故事' : '标准阅读文章'
}

function renderIllustration(data) {
  if (data.image_url) {
    return `<img class="generated-image" src="${data.image_url}" alt="${data.theme} AI illustration" />`
  }
  const statusText =
    data.image_status === 'missing_api_key'
      ? '图片 API Key 未配置：设置 OPENAI_API_KEY 后可生成真实绘本图'
      : `图片生成暂未成功：${data.image_status || 'unknown'}`
  return `
    <div class="image-missing">
      <b>等待生成真实配图</b>
      <span>${statusText}</span>
    </div>
  `
}

function renderReading(data) {
  currentReading = data
  currentResult = null
  $('readingLevel').textContent = data.level
  $('readingMode').textContent = levelName(data.mode)
  $('readingTitle').textContent = data.title
  $('bridgeText').textContent = `${data.level} ${data.bridge.cefr} · ${data.bridge.stage}: ${data.bridge.lesson_idea}`
  $('imagePrompt').textContent = data.illustration_prompt
  $('paragraphs').innerHTML = data.paragraphs
    .map((p) => `<p>${highlight(p, data.target_words)}</p>`)
    .join('')
  $('wordBank').innerHTML = data.word_bank
    .map((w) => `<span class="word" title="${w.meaning}">${w.word}</span>`)
    .join('')
  $('illustration').innerHTML = renderIllustration(data)
  $('startExercise').classList.remove('disabled')
  $('submitBtn').classList.add('disabled')
  unlockNav('reading', 'exercise')
  renderExercises(data.exercises)
  showPage('reading')
}

function renderExercises(exercises) {
  const form = $('exerciseForm')
  form.innerHTML = exercises.map((ex, index) => renderQuestion(ex, index + 1)).join('')
  $('submitBtn').classList.remove('disabled')
}

function renderQuestion(ex, number) {
  if (ex.type === 'matching') {
    return `
      <section class="question" data-type="${ex.type}" data-id="${ex.id}">
        <h3>${number}. ${ex.title}</h3>
        <p>${ex.prompt}</p>
        <div class="matching-grid">
          ${ex.items
            .map(
              (item) => `
                <label>
                  ${item.word}
                  <select name="${ex.id}:${item.word}">
                    <option value="">选择释义</option>
                    ${ex.items.map((opt) => `<option value="${opt.meaning}">${opt.meaning}</option>`).join('')}
                  </select>
                </label>
              `,
            )
            .join('')}
        </div>
      </section>
    `
  }

  if (ex.type === 'cloze' || ex.type === 'mcq') {
    return `
      <section class="question" data-type="${ex.type}" data-id="${ex.id}">
        <h3>${number}. ${ex.title}</h3>
        <p>${ex.prompt}</p>
        <div class="option-list">
          ${ex.options
            .map(
              (option) => `
              <label class="option">
                <input type="radio" name="${ex.id}" value="${option}" />
                ${option}
              </label>
            `,
            )
            .join('')}
        </div>
      </section>
    `
  }

  if (ex.type === 'true_false') {
    return `
      <section class="question" data-type="${ex.type}" data-id="${ex.id}">
        <h3>${number}. ${ex.title}</h3>
        <p>${ex.prompt}</p>
        <div class="option-list">
          <label class="option"><input type="radio" name="${ex.id}" value="true" /> True</label>
          <label class="option"><input type="radio" name="${ex.id}" value="false" /> False</label>
        </div>
      </section>
    `
  }

  return `
    <section class="question" data-type="${ex.type}" data-id="${ex.id}">
      <h3>${number}. ${ex.title}</h3>
      <p>${ex.prompt}</p>
      <input type="text" name="${ex.id}" placeholder="请输入改写后的完整句子" />
    </section>
  `
}

function collectAnswers() {
  const answers = {}
  document.querySelectorAll('.question').forEach((q) => {
    const id = q.dataset.id
    const type = q.dataset.type
    if (type === 'matching') {
      answers[id] = {}
      q.querySelectorAll('select').forEach((select) => {
        const word = select.name.split(':')[1]
        answers[id][word] = select.value
      })
      return
    }
    const radio = q.querySelector(`input[name="${id}"]:checked`)
    const input = q.querySelector(`input[type="text"][name="${id}"]`)
    if (type === 'true_false' && radio) {
      answers[id] = radio.value === 'true'
    } else {
      answers[id] = radio?.value || input?.value || ''
    }
  })
  return answers
}

function renderResult(result) {
  currentResult = result
  $('percent').textContent = `${result.percent}%`
  $('rating').textContent = result.rating
  $('scoreText').textContent = `得分 ${result.score}/${result.total}。系统已根据本篇阅读的目标词汇与题目表现生成复盘。`
  $('reviewList').innerHTML = result.details
    .map(
      (item) => `
        <article class="review-item ${item.correct ? 'good' : 'bad'}">
          <h3>${item.correct ? '✓' : '×'} ${item.title}</h3>
          <p><b>你的答案：</b>${formatAnswer(item.yourAnswer)}</p>
          <p><b>正确答案：</b>${formatAnswer(item.answer)}</p>
          <p>${item.explanation}</p>
        </article>
      `,
    )
    .join('')
  $('weakWords').innerHTML = result.weakWords.map((w) => `<span class="word">${w}</span>`).join('')
  unlockNav('result')
  showPage('result')
}

function formatAnswer(value) {
  if (value === undefined || value === null || value === '') return '未作答'
  if (typeof value === 'object') return Object.entries(value).map(([k, v]) => `${k}: ${v || '未选'}`).join('；')
  return String(value)
}

async function generate() {
  $('generateBtn').textContent = '生成中...'
  $('generateBtn').classList.add('disabled')
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        level: $('level').value,
        mode: $('mode').value,
        theme: $('theme').value.trim() || null,
      }),
    })
    if (!res.ok) throw new Error('生成失败')
    renderReading(await res.json())
  } finally {
    $('generateBtn').textContent = '一键生成素材'
    $('generateBtn').classList.remove('disabled')
  }
}

async function submit() {
  if (!currentReading) return
  $('submitBtn').textContent = '批改中...'
  $('submitBtn').classList.add('disabled')
  try {
    const res = await fetch('/api/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reading_id: currentReading.id, answers: collectAnswers() }),
    })
    if (!res.ok) throw new Error('批改失败')
    renderResult(await res.json())
  } finally {
    $('submitBtn').textContent = '提交批改'
    $('submitBtn').classList.remove('disabled')
  }
}

document.querySelectorAll('[data-jump]').forEach((btn) => {
  btn.addEventListener('click', () => showPage(btn.dataset.jump))
})

$('generateBtn').addEventListener('click', generate)
$('startExercise').addEventListener('click', () => currentReading && showPage('exercise'))
$('submitBtn').addEventListener('click', submit)
$('retryBtn').addEventListener('click', () => currentReading && showPage('exercise'))
$('newBtn').addEventListener('click', () => showPage('home'))
