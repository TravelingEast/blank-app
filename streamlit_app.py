import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Trautonium Emulator",
    page_icon="🎵",
    layout="wide",
)

st.markdown("""
<style>
  .block-container { padding-top: 1rem; }
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

TRAUTONIUM_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #140e04;
    color: #d4a853;
    font-family: 'Courier New', monospace;
    padding: 12px;
    user-select: none;
    -webkit-user-select: none;
  }
  h1 {
    text-align: center;
    font-size: 20px;
    letter-spacing: 6px;
    text-transform: uppercase;
    color: #f0c060;
    text-shadow: 0 0 20px rgba(240,192,96,0.5);
    margin-bottom: 2px;
  }
  .subtitle {
    text-align: center;
    font-size: 10px;
    color: #6a4a22;
    letter-spacing: 2px;
    margin-bottom: 12px;
  }

  /* ── Wire ── */
  #wire-wrap {
    position: relative;
    width: 100%;
    height: 90px;
    background: linear-gradient(to bottom, #080604 0%, #1a1208 40%, #0f0c07 60%, #080604 100%);
    border: 2px solid #3a2810;
    border-radius: 3px;
    cursor: crosshair;
    overflow: hidden;
    box-shadow: inset 0 0 30px rgba(0,0,0,0.7), 0 2px 8px rgba(0,0,0,0.5);
  }
  .rail {
    position: absolute;
    left: 0; right: 0;
    height: 10px;
    background: linear-gradient(to right, #2a1e0a, #4a3820, #6a5030, #4a3820, #2a1e0a);
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.5);
  }
  .rail.top { top: 0; }
  .rail.bot { bottom: 0; }
  #wire-line {
    position: absolute;
    top: 50%;
    left: 24px; right: 24px;
    height: 3px;
    transform: translateY(-50%);
    background: linear-gradient(to right,
      #bb7700, #ddaa00, #ffdd44, #ffcc00, #ddaa00, #ffdd44, #bb7700);
    box-shadow: 0 0 8px rgba(255,200,0,0.9), 0 0 2px rgba(255,255,200,0.5);
    border-radius: 2px;
  }
  .tick {
    position: absolute;
    top: 10px; bottom: 10px;
    width: 1px;
    background: rgba(100,70,20,0.35);
  }
  .tick.octave {
    background: rgba(180,120,30,0.5);
  }
  #cursor-glow {
    position: absolute; top: 0; bottom: 0;
    width: 60px;
    pointer-events: none;
    display: none;
    transform: translateX(-50%);
    background: radial-gradient(ellipse at center,
      rgba(255,210,60,0.25) 0%, transparent 70%);
  }
  #cursor-line {
    position: absolute; top: 0;
    width: 2px; height: 100%;
    background: rgba(255,220,80,0.95);
    box-shadow: 0 0 10px rgba(255,200,50,0.8);
    pointer-events: none;
    display: none;
    transform: translateX(-1px);
  }

  /* ── Pitch labels ── */
  .pitch-labels {
    display: flex;
    justify-content: space-between;
    font-size: 9px;
    color: #5a3a18;
    padding: 3px 24px 6px;
    letter-spacing: 1px;
  }

  /* ── Display ── */
  .display-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 14px;
    background: rgba(0,0,0,0.35);
    border: 1px solid #2e1e0a;
    border-radius: 3px;
    margin-bottom: 8px;
  }
  #note-disp {
    font-size: 38px;
    font-weight: bold;
    color: #ffcc44;
    text-shadow: 0 0 18px rgba(255,200,50,0.8);
    min-width: 90px;
    line-height: 1;
  }
  #freq-disp {
    font-size: 20px;
    color: #b89040;
  }
  #status-disp {
    font-size: 10px;
    color: #5a3a18;
    text-align: right;
    line-height: 1.4;
  }

  /* ── Controls ── */
  .ctrl-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }
  .panel {
    background: rgba(0,0,0,0.3);
    border: 1px solid #2e1e0a;
    border-radius: 3px;
    padding: 8px 10px;
  }
  .panel-title {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #6a4a22;
    border-bottom: 1px solid #2e1e0a;
    padding-bottom: 4px;
    margin-bottom: 6px;
  }
  .row {
    display: flex;
    align-items: center;
    margin-bottom: 5px;
    gap: 6px;
  }
  .lbl {
    font-size: 10px;
    color: #a07840;
    min-width: 72px;
    flex-shrink: 0;
  }
  input[type=range] {
    -webkit-appearance: none;
    appearance: none;
    flex: 1;
    height: 3px;
    background: #3a2810;
    border-radius: 2px;
    outline: none;
    cursor: pointer;
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 13px; height: 13px;
    background: radial-gradient(circle, #e8a830, #a07020);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0 5px rgba(200,150,40,0.5);
  }
  .val {
    font-size: 10px;
    color: #d4a853;
    min-width: 44px;
    text-align: right;
  }
  select {
    background: #1a1208;
    color: #d4a853;
    border: 1px solid #3a2810;
    padding: 2px 5px;
    font-family: monospace;
    font-size: 10px;
    border-radius: 2px;
    cursor: pointer;
    flex: 1;
  }

  /* ── Preset row ── */
  .preset-row {
    display: flex;
    gap: 5px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }
  .preset-btn {
    background: #1e1408;
    color: #c09040;
    border: 1px solid #3a2810;
    padding: 3px 10px;
    font-size: 10px;
    font-family: monospace;
    cursor: pointer;
    border-radius: 2px;
    letter-spacing: 1px;
  }
  .preset-btn:hover { background: #2e2010; color: #f0c060; }

  /* ── Tape deck (recording + loop) ── */
  .tapedeck {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 6px 10px;
    background: rgba(0,0,0,0.3);
    border: 1px solid #2e1e0a;
    border-radius: 3px;
    margin-bottom: 8px;
  }
  .deck-sep {
    width: 1px;
    height: 18px;
    background: #2e1e0a;
    flex-shrink: 0;
  }
  .deck-lbl {
    font-size: 9px;
    letter-spacing: 2px;
    color: #4a3010;
    text-transform: uppercase;
  }
  /* shared button base */
  .tbtn {
    padding: 3px 10px;
    font-size: 10px;
    font-family: monospace;
    cursor: pointer;
    border-radius: 2px;
    letter-spacing: 1px;
    border: 1px solid;
  }
  .tbtn:disabled { opacity: 0.35; cursor: default; }

  /* WAV rec button */
  .wav-btn {
    color: #ff5555;
    border-color: #661818;
    background: #160808;
  }
  .wav-btn:hover:not(:disabled) { background: #220c0c; }
  .wav-btn.armed {
    color: #ff8888;
    background: #2a0808;
    animation: blink 0.75s step-end infinite;
  }
  .wav-timer { font-size: 11px; color: #ff6666; min-width: 38px; }

  /* Loop buttons */
  .loop-rec-btn {
    color: #55dd55;
    border-color: #185518;
    background: #081408;
  }
  .loop-rec-btn:hover:not(:disabled) { background: #0c200c; }
  .loop-rec-btn.armed {
    color: #88ff88;
    background: #0a1e0a;
    animation: blink 0.75s step-end infinite;
  }
  .loop-timer { font-size: 11px; color: #66dd66; min-width: 38px; }

  .loop-clear-btn {
    color: #8888cc;
    border-color: #303066;
    background: #0a0a16;
    display: none;
  }
  .loop-clear-btn:hover { background: #12121e; }

  .loop-info {
    font-size: 10px;
    color: #66aa66;
  }

  /* Loop volume — only visible when loop is loaded */
  .loop-vol-group {
    display: none;
    align-items: center;
    gap: 5px;
    margin-left: auto;
  }
  .loop-vol-group.visible { display: flex; }
  .loop-vol-lbl { font-size: 10px; color: #4a6a4a; white-space: nowrap; }
  #loop-vol { width: 70px; }

  @keyframes blink { 50% { opacity: 0.2; } }

  /* ── Canvas visualizer ── */
  #viz-canvas {
    width: 100%;
    height: 36px;
    display: block;
    margin-bottom: 8px;
    border: 1px solid #1e1408;
    border-radius: 2px;
  }
</style>
</head>
<body>

<h1>Trautonium</h1>
<div class="subtitle">Friedrich Trautwein · Berlin, 1928 &nbsp;|&nbsp; Mixturtrautonium · Oskar Sala</div>

<div id="wire-wrap">
  <div class="rail top"></div>
  <div class="rail bot"></div>
  <div id="wire-line"></div>
  <div id="cursor-glow"></div>
  <div id="cursor-line"></div>
</div>
<div class="pitch-labels" id="pitch-labels"></div>

<canvas id="viz-canvas" height="36"></canvas>

<div class="display-row">
  <div id="note-disp">—</div>
  <div id="freq-disp">— Hz</div>
  <div id="status-disp">Click / touch the wire<br>to begin playing</div>
</div>

<div class="preset-row">
  <button class="preset-btn" onclick="loadPreset('classic')">Classic</button>
  <button class="preset-btn" onclick="loadPreset('mixtur')">Mixturtrautonium</button>
  <button class="preset-btn" onclick="loadPreset('dark')">Dark Bass</button>
  <button class="preset-btn" onclick="loadPreset('bright')">Bright Bell</button>
  <button class="preset-btn" onclick="loadPreset('voice')">Vocal</button>
</div>

<!-- Tape deck: WAV recording + loop store -->
<div class="tapedeck">
  <span class="deck-lbl">WAV</span>
  <button id="wav-btn" class="tbtn wav-btn" onclick="toggleWavRec()">⬤ REC</button>
  <span id="wav-timer" class="wav-timer"></span>

  <div class="deck-sep"></div>

  <span class="deck-lbl">Loop</span>
  <button id="loop-rec-btn" class="tbtn loop-rec-btn" onclick="toggleLoopRec()">⬤ REC</button>
  <span id="loop-timer" class="loop-timer"></span>
  <button id="loop-clear-btn" class="tbtn loop-clear-btn" onclick="clearLoop()">✕ CLEAR</button>
  <span id="loop-info" class="loop-info"></span>

  <div id="loop-vol-group" class="loop-vol-group">
    <span class="loop-vol-lbl">Loop Vol</span>
    <input type="range" id="loop-vol" min="0" max="150" value="100" oninput="setLoopVol()">
    <span class="val" id="loop-vol-v">100%</span>
  </div>
</div>

<div class="ctrl-grid">
  <div class="panel">
    <div class="panel-title">Oscillator &amp; Dynamics</div>
    <div class="row">
      <span class="lbl">Waveform</span>
      <select id="wave" onchange="onCtrl()">
        <option value="sawtooth" selected>Sawtooth</option>
        <option value="square">Square</option>
        <option value="triangle">Triangle</option>
      </select>
    </div>
    <div class="row">
      <span class="lbl">Volume</span>
      <input type="range" id="vol" min="0" max="100" value="70" oninput="onCtrl()">
      <span class="val" id="vol-v">70%</span>
    </div>
    <div class="row">
      <span class="lbl">Attack</span>
      <input type="range" id="atk" min="1" max="600" value="12" oninput="onCtrl()">
      <span class="val" id="atk-v">12ms</span>
    </div>
    <div class="row">
      <span class="lbl">Release</span>
      <input type="range" id="rel" min="10" max="2500" value="220" oninput="onCtrl()">
      <span class="val" id="rel-v">220ms</span>
    </div>
    <div class="row">
      <span class="lbl">Glide</span>
      <input type="range" id="glide" min="1" max="200" value="8" oninput="onCtrl()">
      <span class="val" id="glide-v">8ms</span>
    </div>
  </div>

  <div class="panel">
    <div class="panel-title">Subharmonics (Mixtur)</div>
    <div class="row">
      <span class="lbl">Sub ½</span>
      <input type="range" id="s2" min="0" max="100" value="30" oninput="onCtrl()">
      <span class="val" id="s2-v">30%</span>
    </div>
    <div class="row">
      <span class="lbl">Sub ⅓</span>
      <input type="range" id="s3" min="0" max="100" value="15" oninput="onCtrl()">
      <span class="val" id="s3-v">15%</span>
    </div>
    <div class="row">
      <span class="lbl">Sub ¼</span>
      <input type="range" id="s4" min="0" max="100" value="10" oninput="onCtrl()">
      <span class="val" id="s4-v">10%</span>
    </div>
    <div class="row">
      <span class="lbl">Sub ⅕</span>
      <input type="range" id="s5" min="0" max="100" value="0" oninput="onCtrl()">
      <span class="val" id="s5-v">0%</span>
    </div>
    <div class="row">
      <span class="lbl">Sub ⅙</span>
      <input type="range" id="s6" min="0" max="100" value="0" oninput="onCtrl()">
      <span class="val" id="s6-v">0%</span>
    </div>
  </div>

  <div class="panel">
    <div class="panel-title">Formant Filter I</div>
    <div class="row">
      <span class="lbl">Frequency</span>
      <input type="range" id="f1f" min="80" max="5000" value="800" oninput="onCtrl()">
      <span class="val" id="f1f-v">800Hz</span>
    </div>
    <div class="row">
      <span class="lbl">Resonance Q</span>
      <input type="range" id="f1q" min="1" max="40" value="8" step="0.5" oninput="onCtrl()">
      <span class="val" id="f1q-v">8.0</span>
    </div>
    <div class="row">
      <span class="lbl">Gain</span>
      <input type="range" id="f1g" min="-24" max="24" value="7" oninput="onCtrl()">
      <span class="val" id="f1g-v">+7dB</span>
    </div>
  </div>

  <div class="panel">
    <div class="panel-title">Formant Filter II</div>
    <div class="row">
      <span class="lbl">Frequency</span>
      <input type="range" id="f2f" min="200" max="10000" value="2200" oninput="onCtrl()">
      <span class="val" id="f2f-v">2200Hz</span>
    </div>
    <div class="row">
      <span class="lbl">Resonance Q</span>
      <input type="range" id="f2q" min="1" max="40" value="5" step="0.5" oninput="onCtrl()">
      <span class="val" id="f2q-v">5.0</span>
    </div>
    <div class="row">
      <span class="lbl">Gain</span>
      <input type="range" id="f2g" min="-24" max="24" value="4" oninput="onCtrl()">
      <span class="val" id="f2g-v">+4dB</span>
    </div>
  </div>
</div>

<script>
/* ─── Instrument range ─── */
const MIN_FREQ = 110;
const MAX_FREQ = 1760;
const NOTE_NAMES = ['A','A#','B','C','C#','D','D#','E','F','F#','G','G#'];

/* ─── Tick marks ─── */
(function buildTicks() {
  const wrap = document.getElementById('wire-wrap');
  const margin = 24;
  function place() {
    document.querySelectorAll('.tick').forEach(e => e.remove());
    const w = wrap.offsetWidth;
    for (let semi = 0; semi <= 48; semi++) {
      const ratio = semi / 48;
      const x = margin + ratio * (w - 2 * margin);
      const tick = document.createElement('div');
      tick.className = 'tick' + (semi % 12 === 0 ? ' octave' : '');
      tick.style.left = x + 'px';
      wrap.appendChild(tick);
    }
  }
  place();
  window.addEventListener('resize', place);
  const lbar = document.getElementById('pitch-labels');
  lbar.innerHTML = ['A2','C3','E3','A3','C4','E4','A4','C5','E5','A5','A6']
    .map(n => `<span>${n}</span>`).join('');
})();

/* ─── Audio engine state ─── */
let ctx = null, masterGain = null, loopGain = null, scriptProc = null;
let chain = null, playing = false;
let analyser = null, vizBuf = null;

/* ─── WAV recording state ─── */
let isWavRec = false, wavChunks = [], wavTimerIv = null, wavStart = 0;

/* ─── Loop store state ─── */
let isLoopRec = false, loopChunks = [], loopTimerIv = null, loopStart = 0;
let loopBuffer = null, loopNode = null;

/* ─── Init audio context ─── */
function initCtx() {
  if (ctx) return;
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  masterGain = ctx.createGain();
  masterGain.gain.value = 0.7;

  loopGain = ctx.createGain();
  loopGain.gain.value = 1.0;

  analyser = ctx.createAnalyser();
  analyser.fftSize = 256;
  vizBuf = new Uint8Array(analyser.frequencyBinCount);
  masterGain.connect(analyser);  // viz tap (instrument only)

  // ScriptProcessor: 256-sample pass-through, doubles as recording tap.
  // Both masterGain and loopGain feed into it so WAV captures everything.
  scriptProc = ctx.createScriptProcessor(256, 1, 1);
  scriptProc.onaudioprocess = function(e) {
    const inp = e.inputBuffer.getChannelData(0);
    e.outputBuffer.getChannelData(0).set(inp);   // pass-through
    if (isWavRec)  wavChunks.push(inp.slice());
    if (isLoopRec) loopChunks.push(inp.slice());
  };

  masterGain.connect(scriptProc);
  loopGain.connect(scriptProc);
  scriptProc.connect(ctx.destination);
  startViz();
}

/* ─── Visualiser ─── */
const canvas = document.getElementById('viz-canvas');
const cctx = canvas.getContext('2d');
function startViz() {
  (function frame() {
    requestAnimationFrame(frame);
    const W = canvas.offsetWidth, H = canvas.height;
    canvas.width = W;
    cctx.fillStyle = '#080604';
    cctx.fillRect(0, 0, W, H);
    if (!analyser) return;
    analyser.getByteTimeDomainData(vizBuf);
    cctx.strokeStyle = playing ? '#c8922a' : (loopNode ? '#448844' : '#2e1e08');
    cctx.lineWidth = 1.5;
    cctx.beginPath();
    const step = W / vizBuf.length;
    for (let i = 0; i < vizBuf.length; i++) {
      const y = (vizBuf[i] / 128 - 1) * (H / 2 - 4) + H / 2;
      i === 0 ? cctx.moveTo(0, y) : cctx.lineTo(i * step, y);
    }
    cctx.stroke();
  })();
}

/* ─── WAV encoder (32-bit float PCM, mono) ─── */
function encodeWAV(samples, sampleRate) {
  const bps = 4;
  const dataLen = samples.length * bps;
  const buf = new ArrayBuffer(44 + dataLen);
  const v = new DataView(buf);
  const ws = (off, s) => { for (let i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i)); };
  ws(0, 'RIFF'); v.setUint32(4, 36 + dataLen, true); ws(8, 'WAVE');
  ws(12, 'fmt '); v.setUint32(16, 16, true);
  v.setUint16(20, 3, true);          // IEEE 754 float
  v.setUint16(22, 1, true);          // mono
  v.setUint32(24, sampleRate, true);
  v.setUint32(28, sampleRate * bps, true);
  v.setUint16(32, bps, true);
  v.setUint16(34, 32, true);         // 32-bit
  ws(36, 'data'); v.setUint32(40, dataLen, true);
  for (let i = 0; i < samples.length; i++) v.setFloat32(44 + i * bps, samples[i], true);
  return buf;
}

function mergeChunks(chunks) {
  const total = chunks.reduce((s, c) => s + c.length, 0);
  const out = new Float32Array(total);
  let off = 0;
  for (const c of chunks) { out.set(c, off); off += c.length; }
  return out;
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 6000);
}

/* ─── WAV recording ─── */
function toggleWavRec() {
  if (isWavRec) stopWavRec(); else startWavRec();
}

function startWavRec() {
  initCtx();
  if (ctx.state === 'suspended') ctx.resume();
  wavChunks = [];
  isWavRec = true;
  wavStart = Date.now();
  const btn = document.getElementById('wav-btn');
  btn.textContent = '⏹ STOP';
  btn.classList.add('armed');
  wavTimerIv = setInterval(() => {
    document.getElementById('wav-timer').textContent =
      ((Date.now() - wavStart) / 1000).toFixed(1) + 's';
  }, 100);
}

function stopWavRec() {
  isWavRec = false;
  clearInterval(wavTimerIv);
  const btn = document.getElementById('wav-btn');
  btn.textContent = '⬤ REC';
  btn.classList.remove('armed');
  document.getElementById('wav-timer').textContent = '';
  if (wavChunks.length === 0) return;
  const samples = mergeChunks(wavChunks);
  wavChunks = [];
  const wav = encodeWAV(samples, ctx.sampleRate);
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  triggerDownload(new Blob([wav], { type: 'audio/wav' }), `trautonium_${ts}.wav`);
}

/* ─── Loop store ─── */
function toggleLoopRec() {
  if (isLoopRec) stopLoopRec(); else startLoopRec();
}

function startLoopRec() {
  initCtx();
  if (ctx.state === 'suspended') ctx.resume();
  // Stop any existing loop so we don't bake it into the new one
  // (comment this line out to enable overdub — the loop will be recorded into the new layer)
  stopLoopPlayback();
  loopChunks = [];
  isLoopRec = true;
  loopStart = Date.now();
  const btn = document.getElementById('loop-rec-btn');
  btn.textContent = '⏹ END';
  btn.classList.add('armed');
  loopTimerIv = setInterval(() => {
    document.getElementById('loop-timer').textContent =
      ((Date.now() - loopStart) / 1000).toFixed(1) + 's';
  }, 100);
}

function stopLoopRec() {
  isLoopRec = false;
  clearInterval(loopTimerIv);
  const btn = document.getElementById('loop-rec-btn');
  btn.textContent = '⬤ REC';
  btn.classList.remove('armed');
  document.getElementById('loop-timer').textContent = '';

  if (loopChunks.length === 0) return;

  const samples = mergeChunks(loopChunks);
  loopChunks = [];

  // Build an AudioBuffer from captured samples
  loopBuffer = ctx.createBuffer(1, samples.length, ctx.sampleRate);
  loopBuffer.getChannelData(0).set(samples);

  const dur = (samples.length / ctx.sampleRate).toFixed(2);
  document.getElementById('loop-info').textContent = '↺ ' + dur + 's';
  document.getElementById('loop-clear-btn').style.display = 'inline-block';
  document.getElementById('loop-vol-group').classList.add('visible');

  startLoopPlayback();
}

function startLoopPlayback() {
  stopLoopPlayback();
  if (!loopBuffer) return;
  loopNode = ctx.createBufferSource();
  loopNode.buffer = loopBuffer;
  loopNode.loop = true;
  loopNode.connect(loopGain);
  loopNode.start();
}

function stopLoopPlayback() {
  if (loopNode) {
    try { loopNode.stop(); } catch(e) {}
    loopNode.disconnect();
    loopNode = null;
  }
}

function clearLoop() {
  stopLoopPlayback();
  loopBuffer = null;
  document.getElementById('loop-info').textContent = '';
  document.getElementById('loop-clear-btn').style.display = 'none';
  document.getElementById('loop-vol-group').classList.remove('visible');
}

function setLoopVol() {
  const v = parseInt(document.getElementById('loop-vol').value);
  document.getElementById('loop-vol-v').textContent = v + '%';
  if (loopGain) loopGain.gain.setTargetAtTime(v / 100, ctx.currentTime, 0.02);
}

/* ─── Read UI params ─── */
function P() {
  const v = id => parseFloat(document.getElementById(id).value);
  return {
    wave  : document.getElementById('wave').value,
    vol   : v('vol') / 100,
    atk   : v('atk') / 1000,
    rel   : v('rel') / 1000,
    glide : v('glide') / 1000,
    s2    : v('s2') / 100,  s3: v('s3') / 100,
    s4    : v('s4') / 100,  s5: v('s5') / 100,  s6: v('s6') / 100,
    f1f   : v('f1f'), f1q: v('f1q'), f1g: v('f1g'),
    f2f   : v('f2f'), f2q: v('f2q'), f2g: v('f2g'),
  };
}

function updateLabels(p) {
  const s = (id, val) => { document.getElementById(id).textContent = val; };
  s('vol-v',   Math.round(p.vol * 100) + '%');
  s('atk-v',   Math.round(p.atk * 1000) + 'ms');
  s('rel-v',   Math.round(p.rel * 1000) + 'ms');
  s('glide-v', Math.round(p.glide * 1000) + 'ms');
  s('s2-v',    Math.round(p.s2 * 100) + '%');
  s('s3-v',    Math.round(p.s3 * 100) + '%');
  s('s4-v',    Math.round(p.s4 * 100) + '%');
  s('s5-v',    Math.round(p.s5 * 100) + '%');
  s('s6-v',    Math.round(p.s6 * 100) + '%');
  s('f1f-v',   Math.round(p.f1f) + 'Hz');
  s('f1q-v',   p.f1q.toFixed(1));
  s('f1g-v',   (p.f1g >= 0 ? '+' : '') + Math.round(p.f1g) + 'dB');
  s('f2f-v',   Math.round(p.f2f) + 'Hz');
  s('f2q-v',   p.f2q.toFixed(1));
  s('f2g-v',   (p.f2g >= 0 ? '+' : '') + Math.round(p.f2g) + 'dB');
}

/* ─── Build oscillator chain ─── */
function buildChain(freq) {
  const p = P();
  const t = ctx.currentTime;

  function osc(f, type) {
    const o = ctx.createOscillator();
    o.type = type || p.wave;
    o.frequency.value = f;
    o.start();
    return o;
  }
  function gain(v) { const g = ctx.createGain(); g.gain.value = v; return g; }
  function bpeak(f, q, db) {
    const flt = ctx.createBiquadFilter();
    flt.type = 'peaking'; flt.frequency.value = f; flt.Q.value = q; flt.gain.value = db;
    return flt;
  }

  const oMain = osc(freq);
  const oSub2 = osc(freq / 2, 'sawtooth');
  const oSub3 = osc(freq / 3, 'sawtooth');
  const oSub4 = osc(freq / 4, 'sawtooth');
  const oSub5 = osc(freq / 5, 'sawtooth');
  const oSub6 = osc(freq / 6, 'sawtooth');

  const gMain = gain(1.0);
  const gS2 = gain(p.s2), gS3 = gain(p.s3), gS4 = gain(p.s4),
        gS5 = gain(p.s5), gS6 = gain(p.s6);

  const f1 = bpeak(p.f1f, p.f1q, p.f1g);
  const f2 = bpeak(p.f2f, p.f2q, p.f2g);

  const hp = ctx.createBiquadFilter();
  hp.type = 'highpass'; hp.frequency.value = 35;
  const lp = ctx.createBiquadFilter();
  lp.type = 'lowpass'; lp.frequency.value = 9000; lp.Q.value = 0.6;

  const env = ctx.createGain();
  env.gain.setValueAtTime(0, t);
  env.gain.linearRampToValueAtTime(1, t + Math.max(p.atk, 0.003));

  oMain.connect(gMain); oSub2.connect(gS2); oSub3.connect(gS3);
  oSub4.connect(gS4);   oSub5.connect(gS5); oSub6.connect(gS6);
  [gMain, gS2, gS3, gS4, gS5, gS6].forEach(g => g.connect(f1));
  f1.connect(f2); f2.connect(hp); hp.connect(lp);
  lp.connect(env); env.connect(masterGain);

  return { oMain, oSub2, oSub3, oSub4, oSub5, oSub6,
           gS2, gS3, gS4, gS5, gS6, f1, f2, env };
}

function startNote(freq) {
  if (chain) killChain();
  chain = buildChain(freq);
  playing = true;
}

function setFreq(freq) {
  if (!chain || !playing) return;
  const t = ctx.currentTime, tc = P().glide;
  chain.oMain.frequency.setTargetAtTime(freq,       t, tc);
  chain.oSub2.frequency.setTargetAtTime(freq / 2,   t, tc);
  chain.oSub3.frequency.setTargetAtTime(freq / 3,   t, tc);
  chain.oSub4.frequency.setTargetAtTime(freq / 4,   t, tc);
  chain.oSub5.frequency.setTargetAtTime(freq / 5,   t, tc);
  chain.oSub6.frequency.setTargetAtTime(freq / 6,   t, tc);
}

function stopNote() {
  if (!chain) return;
  const p = P(), t = ctx.currentTime;
  chain.env.gain.cancelScheduledValues(t);
  chain.env.gain.setValueAtTime(chain.env.gain.value, t);
  chain.env.gain.linearRampToValueAtTime(0, t + p.rel);
  [chain.oMain, chain.oSub2, chain.oSub3, chain.oSub4, chain.oSub5, chain.oSub6]
    .forEach(o => o.stop(t + p.rel + 0.05));
  chain = null; playing = false;
}

function killChain() {
  if (!chain) return;
  const t = ctx.currentTime;
  chain.env.gain.setValueAtTime(0, t);
  [chain.oMain, chain.oSub2, chain.oSub3, chain.oSub4, chain.oSub5, chain.oSub6]
    .forEach(o => o.stop(t + 0.01));
  chain = null; playing = false;
}

function onCtrl() {
  const p = P();
  updateLabels(p);
  if (!ctx || !chain) return;
  const t = ctx.currentTime;
  masterGain.gain.setTargetAtTime(p.vol, t, 0.02);
  chain.gS2.gain.setTargetAtTime(p.s2, t, 0.02);
  chain.gS3.gain.setTargetAtTime(p.s3, t, 0.02);
  chain.gS4.gain.setTargetAtTime(p.s4, t, 0.02);
  chain.gS5.gain.setTargetAtTime(p.s5, t, 0.02);
  chain.gS6.gain.setTargetAtTime(p.s6, t, 0.02);
  chain.f1.frequency.setTargetAtTime(p.f1f, t, 0.02);
  chain.f1.Q.setTargetAtTime(p.f1q, t, 0.02);
  chain.f1.gain.setTargetAtTime(p.f1g, t, 0.02);
  chain.f2.frequency.setTargetAtTime(p.f2f, t, 0.02);
  chain.f2.Q.setTargetAtTime(p.f2q, t, 0.02);
  chain.f2.gain.setTargetAtTime(p.f2g, t, 0.02);
}

/* ─── Presets ─── */
function set(id, v) { document.getElementById(id).value = v; }
const PRESETS = {
  classic : { wave:'sawtooth', vol:70, atk:12, rel:220, glide:8,
               s2:30, s3:15, s4:10, s5:0, s6:0,
               f1f:800,  f1q:8,  f1g:7, f2f:2200, f2q:5, f2g:4 },
  mixtur  : { wave:'sawtooth', vol:65, atk:10, rel:280, glide:6,
               s2:50, s3:40, s4:30, s5:20, s6:10,
               f1f:600,  f1q:10, f1g:9, f2f:1800, f2q:8, f2g:6 },
  dark    : { wave:'sawtooth', vol:75, atk:20, rel:600, glide:15,
               s2:60, s3:45, s4:35, s5:25, s6:15,
               f1f:250,  f1q:5,  f1g:10, f2f:700,  f2q:4, f2g:5 },
  bright  : { wave:'triangle', vol:60, atk:5,  rel:1200, glide:4,
               s2:10, s3:5,  s4:0,  s5:0,  s6:0,
               f1f:2400, f1q:14, f1g:12, f2f:5000, f2q:8, f2g:8 },
  voice   : { wave:'sawtooth', vol:65, atk:15, rel:300, glide:10,
               s2:20, s3:8,  s4:5,  s5:0,  s6:0,
               f1f:700,  f1q:12, f1g:10, f2f:2500, f2q:10, f2g:9 },
};

function loadPreset(name) {
  const pr = PRESETS[name];
  if (!pr) return;
  set('wave', pr.wave);
  set('vol', pr.vol);   set('atk', pr.atk); set('rel', pr.rel); set('glide', pr.glide);
  set('s2', pr.s2); set('s3', pr.s3); set('s4', pr.s4); set('s5', pr.s5); set('s6', pr.s6);
  set('f1f', pr.f1f); set('f1q', pr.f1q); set('f1g', pr.f1g);
  set('f2f', pr.f2f); set('f2q', pr.f2q); set('f2g', pr.f2g);
  onCtrl();
}

/* ─── Wire interaction ─── */
const wrap = document.getElementById('wire-wrap');
const cgl  = document.getElementById('cursor-glow');
const cln  = document.getElementById('cursor-line');
const nd   = document.getElementById('note-disp');
const fd   = document.getElementById('freq-disp');
const sd   = document.getElementById('status-disp');

function xToFreq(x) {
  const margin = 24, w = wrap.offsetWidth;
  const ratio = Math.max(0, Math.min(1, (x - margin) / (w - 2 * margin)));
  return MIN_FREQ * Math.pow(MAX_FREQ / MIN_FREQ, ratio);
}

function noteFor(freq) {
  const semi = Math.round(12 * Math.log2(freq / 440));
  const idx  = ((semi % 12) + 12) % 12;
  const oct  = Math.floor((semi + 57) / 12);
  return NOTE_NAMES[idx] + oct;
}

function moveCursor(x) {
  cln.style.left = x + 'px'; cln.style.display = 'block';
  cgl.style.left = x + 'px'; cgl.style.display = 'block';
}
function hideCursor() { cln.style.display = 'none'; cgl.style.display = 'none'; }
function getX(e) {
  const r = wrap.getBoundingClientRect();
  return (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
}

function beginPlay(e) {
  e.preventDefault();
  initCtx();
  if (ctx.state === 'suspended') ctx.resume();
  const x = getX(e), freq = xToFreq(x);
  moveCursor(x);
  nd.textContent = noteFor(freq);
  fd.textContent = freq.toFixed(1) + ' Hz';
  sd.textContent = 'Playing…';
  masterGain.gain.value = P().vol;
  startNote(freq);
}

function movePlay(e) {
  if (!playing) return;
  const x = getX(e), freq = xToFreq(x);
  moveCursor(x);
  nd.textContent = noteFor(freq);
  fd.textContent = freq.toFixed(1) + ' Hz';
  setFreq(freq);
}

function endPlay(e) {
  if (e) e.preventDefault();
  hideCursor();
  nd.textContent = '—';
  fd.textContent = '— Hz';
  sd.textContent = 'Click / touch the wire\nto begin playing';
  stopNote();
}

wrap.addEventListener('mousedown', beginPlay);
wrap.addEventListener('mousemove', movePlay);
wrap.addEventListener('mouseup',   endPlay);
wrap.addEventListener('mouseleave', e => { if (playing) endPlay(e); });
wrap.addEventListener('touchstart', beginPlay, { passive: false });
wrap.addEventListener('touchmove',  movePlay,  { passive: false });
wrap.addEventListener('touchend',   endPlay,   { passive: false });

/* ─── Init ─── */
updateLabels(P());
</script>
</body>
</html>
"""

components.html(TRAUTONIUM_HTML, height=720, scrolling=False)

st.markdown("---")
st.markdown(
    """
    **About the Trautonium** — Invented by Friedrich Trautwein in Berlin in 1928, the Trautonium
    was one of the earliest electronic instruments. The player presses a resistive wire against a
    metal rail to control pitch continuously — no fixed keys. Oskar Sala later developed the
    **Mixturtrautonium**, adding subharmonic generators that divide the oscillator frequency by
    integers (½, ⅓, ¼…) to create rich, organ-like timbres. Sala used it to compose the iconic
    bird sounds in Hitchcock's *The Birds* (1963).
    """,
    unsafe_allow_html=False,
)
