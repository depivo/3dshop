<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../api/client'

const ALLOWED_EXTENSIONS = ['.stl', '.3mf']
const MAX_SIZE_BYTES = 300 * 1024 * 1024

const form = reactive({
  name: '',
  phone: '',
  comment: '',
  files: [],
})

const submitting = ref(false)
const success = ref(false)
const orderId = ref('')
const errorMessage = ref('')

function fileExtension(filename) {
  const idx = filename.lastIndexOf('.')
  return idx === -1 ? '' : filename.slice(idx).toLowerCase()
}

function onFileChange(event) {
  const selected = Array.from(event.target.files)
  event.target.value = ''
  if (selected.length === 0) return

  for (const file of selected) {
    const ext = fileExtension(file.name)
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      errorMessage.value = `Файл «${file.name}»: дозволені лише .stl і .3mf`
      return
    }
    if (file.size > MAX_SIZE_BYTES) {
      errorMessage.value = `Файл «${file.name}» занадто великий (максимум 300 МБ)`
      return
    }
  }

  errorMessage.value = ''
  form.files.push(...selected)
}

function removeFile(index) {
  form.files.splice(index, 1)
}

async function handleSubmit() {
  errorMessage.value = ''

  if (!form.name.trim() || !form.phone.trim()) {
    errorMessage.value = "Заповніть ім'я і телефон"
    return
  }
  if (form.files.length === 0) {
    errorMessage.value = 'Додайте хоча б один файл моделі (.stl або .3mf)'
    return
  }

  const payload = new FormData()
  payload.append('name', form.name.trim())
  payload.append('phone', form.phone.trim())
  if (form.comment.trim()) payload.append('comment', form.comment.trim())
  form.files.forEach((file) => payload.append('files', file))

  submitting.value = true
  try {
    const { data } = await api.post('/orders', payload)
    orderId.value = data.id
    success.value = true
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Не вдалося надіслати замовлення. Спробуйте ще раз.'
  } finally {
    submitting.value = false
  }
}

const rootEl = ref(null)

onMounted(() => {
  // Hero: animated toolpath spiral, like a slicer preview.
  const canvas = rootEl.value.querySelector('#heroCanvas')
  const ctx = canvas.getContext('2d')
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  const size = 600
  canvas.width = size * dpr
  canvas.height = size * dpr
  ctx.scale(dpr, dpr)

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const cx = size / 2
  const cy = size / 2
  const turns = 9
  const maxR = size * 0.38
  const totalPoints = 1400

  function colorAt(t) {
    const cool = [87, 199, 227]
    const hot = [255, 107, 61]
    const r = Math.round(cool[0] + (hot[0] - cool[0]) * t)
    const g = Math.round(cool[1] + (hot[1] - cool[1]) * t)
    const b = Math.round(cool[2] + (hot[2] - cool[2]) * t)
    return `rgb(${r},${g},${b})`
  }

  function pointAt(i) {
    const t = i / totalPoints
    const angle = t * Math.PI * 2 * turns
    const r = t * maxR
    return [cx + Math.cos(angle) * r, cy + Math.sin(angle) * r * 0.92]
  }

  function drawGrid() {
    ctx.strokeStyle = 'rgba(255,255,255,0.05)'
    ctx.lineWidth = 1
    for (let x = 0; x <= size; x += 30) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, size); ctx.stroke()
    }
    for (let y = 0; y <= size; y += 30) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(size, y); ctx.stroke()
    }
    ctx.strokeStyle = 'rgba(255,255,255,0.09)'
    ctx.beginPath(); ctx.arc(cx, cy, maxR + 14, 0, Math.PI * 2); ctx.stroke()
  }

  function render(upTo) {
    ctx.clearRect(0, 0, size, size)
    drawGrid()
    ctx.lineWidth = 1.6
    ctx.lineCap = 'round'
    let prev = pointAt(0)
    for (let i = 1; i <= upTo; i++) {
      const p = pointAt(i)
      ctx.strokeStyle = colorAt(i / totalPoints)
      ctx.beginPath()
      ctx.moveTo(prev[0], prev[1])
      ctx.lineTo(p[0], p[1])
      ctx.stroke()
      prev = p
    }
    if (upTo > 0) {
      const tip = pointAt(upTo)
      ctx.fillStyle = '#ff6b3d'
      ctx.shadowColor = '#ff6b3d'
      ctx.shadowBlur = 12
      ctx.beginPath()
      ctx.arc(tip[0], tip[1], 4, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0
    }
  }

  if (reduced) {
    render(totalPoints)
  } else {
    let frame = 0
    const speed = 9
    const loop = () => {
      frame += speed
      if (frame > totalPoints) frame = totalPoints
      render(frame)
      if (frame < totalPoints) {
        requestAnimationFrame(loop)
      } else {
        setTimeout(() => { frame = 0; loop() }, 1800)
      }
    }
    loop()
  }

  // Case thumbnails: procedural wireframe "part" shapes, deterministic per seed.
  function mulberry32(seed) {
    return function () {
      let t = (seed += 0x6D2B79F5)
      t = Math.imul(t ^ (t >>> 15), t | 1)
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
  }

  rootEl.value.querySelectorAll('.caseCanvas').forEach((caseCanvas) => {
    const seed = parseInt(caseCanvas.dataset.seed, 10) * 1000 + 7
    const rand = mulberry32(seed)
    const parent = caseCanvas.parentElement
    const w = parent.clientWidth
    const h = parent.clientHeight
    const caseDpr = Math.min(window.devicePixelRatio || 1, 2)
    caseCanvas.width = w * caseDpr
    caseCanvas.height = h * caseDpr
    const caseCtx = caseCanvas.getContext('2d')
    caseCtx.scale(caseDpr, caseDpr)

    caseCtx.fillStyle = '#1a1d24'
    caseCtx.fillRect(0, 0, w, h)

    caseCtx.strokeStyle = 'rgba(255,255,255,0.045)'
    for (let x = 0; x < w; x += 22) { caseCtx.beginPath(); caseCtx.moveTo(x, 0); caseCtx.lineTo(x, h); caseCtx.stroke() }
    for (let y = 0; y < h; y += 22) { caseCtx.beginPath(); caseCtx.moveTo(0, y); caseCtx.lineTo(w, y); caseCtx.stroke() }

    const partCx = w / 2
    const partCy = h / 2 + 6
    const points = 7
    const baseR = Math.min(w, h) * 0.28
    const verts = []
    for (let i = 0; i < points; i++) {
      const a = (i / points) * Math.PI * 2
      const r = baseR * (0.65 + rand() * 0.5)
      verts.push([partCx + Math.cos(a) * r, partCy + Math.sin(a) * r * 0.85])
    }

    caseCtx.strokeStyle = 'rgba(87,199,227,0.55)'
    caseCtx.lineWidth = 1.2
    caseCtx.beginPath()
    verts.forEach((v, i) => (i === 0 ? caseCtx.moveTo(v[0], v[1]) : caseCtx.lineTo(v[0], v[1])))
    caseCtx.closePath()
    caseCtx.stroke()

    caseCtx.strokeStyle = 'rgba(255,107,61,0.4)'
    verts.forEach((v) => {
      caseCtx.beginPath()
      caseCtx.moveTo(partCx, partCy)
      caseCtx.lineTo(v[0], v[1])
      caseCtx.stroke()
    })

    caseCtx.fillStyle = '#ff6b3d'
    caseCtx.beginPath()
    caseCtx.arc(partCx, partCy, 2.5, 0, Math.PI * 2)
    caseCtx.fill()
  })
})
</script>

<template>
  <div ref="rootEl" class="landing">
    <header>
      <div class="wrap nav">
        <div class="wordmark">ЦЕХ<small>3D-ДРУК НА ЗАМОВЛЕННЯ</small></div>
        <nav class="navlinks">
          <a href="#how">Як це працює</a>
          <a href="#why">Чому ми</a>
          <a href="#materials">Матеріали</a>
          <a href="#cases">Кейси</a>
          <a href="#order">Замовити</a>
        </nav>
        <a href="#order" class="btn btn-primary btn-sm">Завантажити модель</a>
      </div>
    </header>

    <main>
      <section class="hero">
        <div class="wrap">
          <div>
            <span class="eyebrow">приймаємо замовлення · друкуємо самі</span>
            <h1>Файл сьогодні —<br /><em>деталь</em> післязавтра.</h1>
            <p class="hero-lede">
              Завантажуєте STL або 3MF, ми рахуємо вартість і друкуємо самі, на своїх принтерах.
              Без каталогів, без магазину — просто модель, розмова і готова деталь у руках.
            </p>
            <div class="hero-cta">
              <a href="#order" class="btn btn-primary">Надіслати модель на розрахунок</a>
              <a href="#how" class="btn btn-ghost">Як це влаштовано</a>
            </div>
            <div class="spec-row">
              <span>Шар від <span class="val">0.05 мм</span></span>
              <span>Матеріали <span class="val">PLA · PETG · ABS · Resin</span></span>
              <span>Розрахунок ціни <span class="val">протягом дня</span></span>
            </div>
          </div>
          <div class="hero-canvas-panel bracket">
            <span class="bl"></span><span class="br"></span>
            <canvas id="heroCanvas" width="600" height="600" aria-hidden="true"></canvas>
            <div class="hero-canvas-caption">TOOLPATH.PREVIEW <b>· LAYER 184/240</b></div>
          </div>
        </div>
      </section>

      <hr class="divider" />

      <section id="how">
        <div class="wrap">
          <div class="section-head">
            <span class="eyebrow">процес</span>
            <h2>Три кроки від файлу до деталі</h2>
            <p>Жодного автоматичного кошика — на іншому кінці завжди людина, яка дивиться модель і рахує друк вручну.</p>
          </div>
          <div class="steps">
            <div class="step">
              <span class="idx">01 / ЗАВАНТАЖЕННЯ</span>
              <h3>Надсилаєте модель</h3>
              <p>STL або 3MF, ім'я і телефон для зв'язку. Можна додати коментар — матеріал, колір, терміни.</p>
            </div>
            <div class="step">
              <span class="idx">02 / РОЗРАХУНОК</span>
              <h3>Ми рахуємо і телефонуємо</h3>
              <p>Дивимось геометрію, прикидаємо час і витрату матеріалу, називаємо ціну і термін — зазвичай протягом дня.</p>
            </div>
            <div class="step">
              <span class="idx">03 / ДРУК</span>
              <h3>Друкуємо і віддаємо</h3>
              <p>Після підтвердження ставимо в чергу на друк. Готово — забираєте або надсилаємо поштою.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="why">
        <div class="wrap">
          <div class="section-head">
            <span class="eyebrow">чому ми</span>
            <h2>Майстерня, а не маркетплейс</h2>
            <p>Ми самі друкуємо кожне замовлення — тому відповідаємо за якість і тримаємо розумні терміни.</p>
          </div>
          <div class="features">
            <div class="feature bracket">
              <span class="bl"></span><span class="br"></span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 4h16v16H4z"/><path d="M4 9h16M9 9v11"/></svg>
              <h3>Будь-яка геометрія</h3>
              <p>Від дрібних деталей і прототипів до великих функціональних корпусів — друкуємо те, що не беруть у типових сервісах.</p>
            </div>
            <div class="feature bracket">
              <span class="bl"></span><span class="br"></span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg>
              <h3>Чесні терміни</h3>
              <p>Називаємо реальний час друку, а не «постараємось встигнути». Якщо черга — попереджаємо заздалегідь.</p>
            </div>
            <div class="feature bracket">
              <span class="bl"></span><span class="br"></span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 12h4l3 8 4-16 3 8h4"/></svg>
              <h3>Прозора ціна</h3>
              <p>Ціна — за матеріал і час друку, без націнки «на око». Рахуємо при вас, пояснюємо, з чого вона складається.</p>
            </div>
            <div class="feature bracket">
              <span class="bl"></span><span class="br"></span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
              <h3>Живий зв'язок</h3>
              <p>Жодних тікетів і ботів на етапі розрахунку — телефонуємо або пишемо самі, обговорюємо деталі голосом.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="materials">
        <div class="wrap">
          <div class="section-head">
            <span class="eyebrow">матеріали</span>
            <h2>Друкуємо на чотирьох пластиках</h2>
            <p>Матеріал підбираємо під задачу — якщо не впевнені, який потрібен, підкажемо при розрахунку замовлення.</p>
          </div>
          <div class="materials">
            <div class="material-card bracket">
              <span class="bl"></span><span class="br"></span>
              <div class="material-head">
                <div class="spool" style="background: conic-gradient(#ff6b3d 0turn, #ffb199 0.5turn, #ff6b3d 1turn);"></div>
                <div>
                  <div class="material-name">PLA</div>
                  <div class="material-tag">БАЗОВИЙ · БУДЬ-ЯКИЙ КОЛІР</div>
                </div>
              </div>
              <p class="desc">Найдоступніший варіант для прототипів, сувенірів і декору. Добре тримає дрібну деталізацію.</p>
              <div class="spec-meter">
                <div class="spec-meter-row"><span class="spec-meter-label">МІЦНІСТЬ</span><div class="spec-meter-track"><div class="spec-meter-fill" style="width:60%; background:var(--accent-cool);"></div></div></div>
                <div class="spec-meter-row"><span class="spec-meter-label">ТЕРМОСТІЙКІСТЬ</span><div class="spec-meter-track"><div class="spec-meter-fill" style="width:40%; background:var(--accent-hot);"></div></div></div>
              </div>
            </div>

            <div class="material-card bracket">
              <span class="bl"></span><span class="br"></span>
              <div class="material-head">
                <div class="spool" style="background: conic-gradient(#57c7e3 0turn, #bdeaf6 0.5turn, #57c7e3 1turn);"></div>
                <div>
                  <div class="material-name">PETG</div>
                  <div class="material-tag">ФУНКЦІОНАЛЬНИЙ · ВОЛОГОСТІЙКИЙ</div>
                </div>
              </div>
              <p class="desc">Міцніший і пластичніший за PLA, не боїться вологи. Гарний вибір для деталей, які реально експлуатують.</p>
              <div class="spec-meter">
                <div class="spec-meter-row"><span class="spec-meter-label">МІЦНІСТЬ</span><div class="spec-meter-track"><div class="spec-meter-fill" style="width:78%; background:var(--accent-cool);"></div></div></div>
                <div class="spec-meter-row"><span class="spec-meter-label">ТЕРМОСТІЙКІСТЬ</span><div class="spec-meter-track"><div class="spec-meter-fill" style="width:62%; background:var(--accent-hot);"></div></div></div>
              </div>
            </div>

            <div class="material-card bracket">
              <span class="bl"></span><span class="br"></span>
              <div class="material-head">
                <div class="spool" style="background: conic-gradient(#9aa0ac 0turn, #4a4f5a 0.5turn, #9aa0ac 1turn);"></div>
                <div>
                  <div class="material-name">ABS</div>
                  <div class="material-tag">УДАРОСТІЙКИЙ · ТЕРМОСТІЙКИЙ</div>
                </div>
              </div>
              <p class="desc">Тримає удар і нагрів краще за інших. Підходить для корпусів, кріплення і деталей поряд із теплом.</p>
              <div class="spec-meter">
                <div class="spec-meter-row"><span class="spec-meter-label">МІЦНІСТЬ</span><div class="spec-meter-track"><div class="spec-meter-fill" style="width:82%; background:var(--accent-cool);"></div></div></div>
                <div class="spec-meter-row"><span class="spec-meter-label">ТЕРМОСТІЙКІСТЬ</span><div class="spec-meter-track"><div class="spec-meter-fill" style="width:85%; background:var(--accent-hot);"></div></div></div>
              </div>
            </div>

            <div class="material-card bracket">
              <span class="bl"></span><span class="br"></span>
              <div class="material-head">
                <div class="spool" style="background: conic-gradient(#ff6b3d 0turn, #57c7e3 0.5turn, #ff6b3d 1turn);"></div>
                <div>
                  <div class="material-name">Resin</div>
                  <div class="material-tag">SLA · ВИСОКА ДЕТАЛІЗАЦІЯ</div>
                </div>
              </div>
              <p class="desc">Для мініатюр і точної геометрії — де важлива гладка поверхня і дрібні деталі, а не міцність.</p>
              <div class="spec-meter">
                <div class="spec-meter-row"><span class="spec-meter-label">МІЦНІСТЬ</span><div class="spec-meter-track"><div class="spec-meter-fill" style="width:45%; background:var(--accent-cool);"></div></div></div>
                <div class="spec-meter-row"><span class="spec-meter-label">ТЕРМОСТІЙКІСТЬ</span><div class="spec-meter-track"><div class="spec-meter-fill" style="width:38%; background:var(--accent-hot);"></div></div></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="cases">
        <div class="wrap">
          <div class="section-head">
            <span class="eyebrow">кейси</span>
            <h2>Що друкували нещодавно</h2>
            <p>Декілька прикладів з останніх замовлень — від прототипів до готових функціональних деталей.</p>
          </div>
          <div class="cases">
            <div class="case bracket"><span class="bl"></span><span class="br"></span><canvas class="caseCanvas" data-seed="1"></canvas><div class="case-label">Корпус електроніки · PETG</div></div>
            <div class="case bracket"><span class="bl"></span><span class="br"></span><canvas class="caseCanvas" data-seed="2"></canvas><div class="case-label">Кронштейн кріплення · PLA+</div></div>
            <div class="case bracket"><span class="bl"></span><span class="br"></span><canvas class="caseCanvas" data-seed="3"></canvas><div class="case-label">Прототип механізму · ABS</div></div>
            <div class="case bracket"><span class="bl"></span><span class="br"></span><canvas class="caseCanvas" data-seed="4"></canvas><div class="case-label">Мініатюра · Resin</div></div>
            <div class="case bracket"><span class="bl"></span><span class="br"></span><canvas class="caseCanvas" data-seed="5"></canvas><div class="case-label">Кріплення під замовлення · ABS</div></div>
          </div>
        </div>
      </section>

      <section id="order" class="order-section">
        <div class="wrap order-grid">
          <div class="order-info">
            <span class="eyebrow">оформити замовлення</span>
            <h2>Надішліть модель — почнемо рахувати</h2>
            <p>Заповніть форму і додайте файл. Ми зв'яжемося з вами по телефону, щойно прикинемо вартість.</p>
            <div class="order-info-list">
              <div class="order-info-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 4h16v16H4z"/><path d="M9 4v16"/></svg>
                <span>Приймаємо файли формату .stl і .3mf, до 300 МБ</span>
              </div>
              <div class="order-info-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg>
                <span>Відповідаємо протягом робочого дня</span>
              </div>
              <div class="order-info-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
                <span>Ціну і терміни узгоджуємо голосом — без передоплати наосліп</span>
              </div>
            </div>
          </div>

          <div v-if="success" class="order-form bracket success-panel">
            <span class="bl"></span><span class="br"></span>
            <span class="eyebrow">заявку прийнято</span>
            <h3>Заявку №{{ orderId.slice(0, 8) }} надіслано</h3>
            <p>Ми подивимось модель і зв'яжемося з вами по телефону {{ form.phone }}, щойно прикинемо вартість.</p>
          </div>

          <form v-else class="order-form bracket" @submit.prevent="handleSubmit">
            <span class="bl"></span><span class="br"></span>
            <div class="field-row">
              <div class="field">
                <label for="f-name">Ім'я</label>
                <input id="f-name" v-model="form.name" type="text" placeholder="Як до вас звертатися" />
              </div>
              <div class="field">
                <label for="f-phone">Телефон</label>
                <input id="f-phone" v-model="form.phone" type="tel" placeholder="+380 __ ___ __ __" />
              </div>
            </div>

            <div class="field">
              <label for="f-file">Файли моделі</label>
              <label class="dropzone" for="f-file" tabindex="0">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3v12m0-12 4 4m-4-4-4 4"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>
                <span class="dz-title">Перетягніть файли або натисніть, щоб вибрати</span>
                <span class="dz-sub">.STL · .3MF — ДО 300 МБ ЗА ФАЙЛ, МОЖНА КІЛЬКА</span>
              </label>
              <input id="f-file" type="file" accept=".stl,.3mf" multiple class="visually-hidden" @change="onFileChange" />

              <ul v-if="form.files.length" class="file-list">
                <li v-for="(file, index) in form.files" :key="`${file.name}-${index}`" class="file-list-item">
                  <span class="file-list-name">{{ file.name }}</span>
                  <button type="button" class="file-list-remove" aria-label="Прибрати файл" @click="removeFile(index)">✕</button>
                </li>
              </ul>
            </div>

            <div class="field">
              <label for="f-comment">Коментар</label>
              <textarea id="f-comment" v-model="form.comment" placeholder="Матеріал, колір, кількість, терміни — все, що важливо знати перед розрахунком"></textarea>
            </div>

            <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

            <div class="form-submit">
              <span class="form-hint">Натискаючи «Надіслати», ви погоджуєтесь на обробку даних для зв'язку щодо замовлення</span>
              <button type="submit" class="btn btn-primary" :disabled="submitting">
                {{ submitting ? 'Надсилаємо…' : 'Надіслати на розрахунок' }}
              </button>
            </div>
          </form>
        </div>
      </section>
    </main>

    <footer>
      <div class="wrap">
        <div class="footer-row">
          <div class="wordmark">ЦЕХ<small>3D-ДРУК НА ЗАМОВЛЕННЯ</small></div>
          <div class="footer-links">
            <a href="#">Telegram</a>
            <a href="#">Viber</a>
            <a href="tel:+380000000000">+380 00 000 00 00</a>
          </div>
        </div>
        <div class="footer-fine">© ЦЕХ — МАЙСТЕРНЯ 3D-ДРУКУ. ВСІ ЗАМОВЛЕННЯ ДРУКУЮТЬСЯ ВРУЧНУ, БЕЗ АВТОМАТИЗАЦІЇ.</div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.landing {
  position: relative;
}
.landing::before {
  content: "";
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse 900px 600px at 50% -10%, rgba(255, 107, 61, 0.08), transparent 60%);
  pointer-events: none;
  z-index: 0;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

header {
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
  background: rgba(18, 20, 26, 0.82);
  border-bottom: 1px solid var(--border);
}
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
}
.wordmark {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.wordmark small {
  font-size: 0.65rem;
  color: var(--text-faint);
  letter-spacing: 0.1em;
  font-weight: 500;
}
.navlinks {
  display: flex;
  gap: 32px;
  font-size: 0.88rem;
}
.navlinks a {
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.15s ease;
  padding: 4px 2px;
}
.navlinks a:hover,
.navlinks a:focus-visible {
  color: var(--text);
}
.navlinks a:focus-visible {
  outline: 1px solid var(--accent-cool);
  outline-offset: 4px;
}

.hero {
  padding: clamp(64px, 10vw, 128px) 0 80px;
}
.hero :deep(.wrap) {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 48px;
  align-items: center;
}
.hero h1 {
  font-size: clamp(2.4rem, 1.7rem + 2.8vw, 4.2rem);
  line-height: 1.04;
  margin: 20px 0 24px;
}
.hero h1 em {
  font-style: normal;
  color: var(--accent-hot);
}
.hero-lede {
  font-size: 1.08rem;
  line-height: 1.6;
  color: var(--text-muted);
  max-width: 46ch;
  margin-bottom: 36px;
}
.hero-cta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 40px;
}
.spec-row {
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
  font-family: var(--font-display);
  font-size: 0.76rem;
  color: var(--text-faint);
}
.spec-row .val {
  color: var(--text);
  font-weight: 700;
}
.spec-row span {
  display: block;
}
.hero-canvas-panel {
  aspect-ratio: 1 / 1;
  position: relative;
  padding: 18px;
}
.hero-canvas-panel canvas {
  width: 100%;
  height: 100%;
  display: block;
}
.hero-canvas-caption {
  position: absolute;
  left: 18px;
  bottom: 14px;
  font-family: var(--font-display);
  font-size: 0.68rem;
  color: var(--text-faint);
  letter-spacing: 0.04em;
}
.hero-canvas-caption b {
  color: var(--accent-cool);
  font-weight: 700;
}

section {
  padding: clamp(56px, 8vw, 96px) 0;
  position: relative;
}
.section-head {
  margin-bottom: 48px;
  max-width: 60ch;
}
.section-head h2 {
  font-size: clamp(1.6rem, 1.3rem + 1.2vw, 2.4rem);
  margin-top: 14px;
}
.section-head p {
  color: var(--text-muted);
  margin-top: 14px;
  font-size: 1rem;
  line-height: 1.6;
}

.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
}
.step {
  background: var(--bg);
  padding: 32px 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.step .idx {
  font-family: var(--font-display);
  font-size: 0.76rem;
  color: var(--accent-hot);
  letter-spacing: 0.08em;
}
.step h3 {
  font-size: 1.12rem;
  font-weight: 700;
}
.step p {
  color: var(--text-muted);
  font-size: 0.92rem;
  line-height: 1.55;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}
.feature {
  padding: 26px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.feature svg {
  width: 22px;
  height: 22px;
  color: var(--accent-cool);
}
.feature h3 {
  font-size: 1rem;
  font-weight: 700;
}
.feature p {
  color: var(--text-muted);
  font-size: 0.88rem;
  line-height: 1.55;
}

.materials {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.material-card {
  padding: 26px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.material-head {
  display: flex;
  align-items: center;
  gap: 14px;
}
.spool {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}
.spool::after {
  content: "";
  position: absolute;
  inset: 15px;
  border-radius: 50%;
  background: var(--bg-elevated);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}
.material-name {
  font-weight: 700;
  font-size: 1rem;
}
.material-tag {
  font-family: var(--font-display);
  font-size: 0.7rem;
  color: var(--text-faint);
  letter-spacing: 0.06em;
}
.material-card p.desc {
  color: var(--text-muted);
  font-size: 0.88rem;
  line-height: 1.55;
}
.spec-meter {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.spec-meter-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.spec-meter-label {
  font-family: var(--font-display);
  font-size: 0.68rem;
  color: var(--text-faint);
  width: 108px;
  flex-shrink: 0;
}
.spec-meter-track {
  flex: 1;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}
.spec-meter-fill {
  height: 100%;
  border-radius: 2px;
}

.cases {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.case {
  aspect-ratio: 4 / 3;
  position: relative;
  overflow: hidden;
}
.case canvas {
  width: 100%;
  height: 100%;
  display: block;
}
.case-label {
  position: absolute;
  left: 14px;
  bottom: 12px;
  font-family: var(--font-display);
  font-size: 0.74rem;
  color: var(--text);
  background: rgba(18, 20, 26, 0.7);
  padding: 4px 8px;
  border: 1px solid var(--border);
}

.order-section {
  background: var(--bg-elevated);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.order-grid {
  display: grid;
  grid-template-columns: 0.85fr 1.15fr;
  gap: 56px;
  align-items: start;
}
.order-info h2 {
  font-size: clamp(1.6rem, 1.3rem + 1vw, 2.2rem);
}
.order-info p {
  color: var(--text-muted);
  margin-top: 16px;
  line-height: 1.6;
  font-size: 0.98rem;
  max-width: 40ch;
}
.order-info-list {
  margin-top: 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.order-info-item {
  display: flex;
  gap: 12px;
  font-size: 0.88rem;
  color: var(--text-muted);
  align-items: flex-start;
}
.order-info-item svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--accent-hot);
}

.order-form {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.success-panel {
  min-height: 220px;
  justify-content: center;
}
.success-panel h3 {
  margin: 14px 0 10px;
  font-size: 1.3rem;
}
.success-panel p {
  color: var(--text-muted);
  line-height: 1.6;
}

.dropzone {
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius);
  padding: 28px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
  position: relative;
}
.dropzone:hover,
.dropzone:focus-visible {
  border-color: var(--accent-hot);
  background: var(--accent-hot-soft);
}
.dropzone svg {
  width: 26px;
  height: 26px;
  color: var(--accent-hot);
}
.dropzone .dz-title {
  font-size: 0.92rem;
  font-weight: 600;
}
.dropzone .dz-sub {
  font-size: 0.78rem;
  color: var(--text-faint);
  font-family: var(--font-display);
}

.file-list {
  list-style: none;
  margin: 4px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.file-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-size: 0.82rem;
}
.file-list-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-list-remove {
  flex-shrink: 0;
  background: none;
  border: none;
  color: var(--text-faint);
  cursor: pointer;
  font-size: 0.9rem;
  line-height: 1;
  padding: 2px 4px;
}
.file-list-remove:hover {
  color: var(--accent-hot);
}

.form-submit {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.form-hint {
  font-size: 0.78rem;
  color: var(--text-faint);
}

footer {
  border-top: 1px solid var(--border);
  padding: 40px 0;
}
.footer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}
.footer-links {
  display: flex;
  gap: 24px;
  font-size: 0.86rem;
  color: var(--text-muted);
}
.footer-links a {
  text-decoration: none;
}
.footer-links a:hover {
  color: var(--accent-cool);
}
.footer-fine {
  font-family: var(--font-display);
  font-size: 0.72rem;
  color: var(--text-faint);
  margin-top: 20px;
}

@media (max-width: 900px) {
  .hero :deep(.wrap) {
    grid-template-columns: 1fr;
  }
  .hero-canvas-panel {
    aspect-ratio: 16 / 10;
    order: -1;
  }
  .steps {
    grid-template-columns: 1fr;
  }
  .order-grid {
    grid-template-columns: 1fr;
  }
  .navlinks {
    display: none;
  }
}
</style>
