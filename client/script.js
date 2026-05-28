const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const submitBtn = document.getElementById('submitBtn');
const clearBtn = document.getElementById('clearBtn');
const undoBtn = document.getElementById('undoBtn');
const resultImg = document.getElementById('result');
const resultWrapper = document.getElementById('resultWrapper');
const loading = document.getElementById('loading');

// Configuration
const SERVER_URL = 'http://localhost:8000';   // или задать через window.__SERVER_URL__

// Drawing state
let isDrawing = false;
let lastX = 0, lastY = 0;
let history = [];

// Setup canvas background
ctx.fillStyle = 'white';
ctx.fillRect(0, 0, canvas.width, canvas.height);
ctx.strokeStyle = 'black';
ctx.lineWidth = 3;
ctx.lineCap = 'round';
ctx.lineJoin = 'round';

saveState();

// --- Drawing handlers ---
function getPos(e) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: (e.offsetX / rect.width) * canvas.width,
    y: (e.offsetY / rect.height) * canvas.height,
  };
}

function startDraw(e) {
  isDrawing = true;
  const pos = getPos(e);
  lastX = pos.x; lastY = pos.y;
}

function draw(e) {
  if (!isDrawing) return;
  const pos = getPos(e);
  ctx.beginPath();
  ctx.moveTo(lastX, lastY);
  ctx.lineTo(pos.x, pos.y);
  ctx.stroke();
  lastX = pos.x; lastY = pos.y;
}

function stopDraw() {
  if (isDrawing) {
    isDrawing = false;
    saveState();
  }
}

function saveState() {
  history.push(canvas.toDataURL());
  if (history.length > 20) history.shift();
  undoBtn.disabled = false;
}

canvas.addEventListener('mousedown', startDraw);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', stopDraw);
canvas.addEventListener('mouseleave', stopDraw);

canvas.addEventListener('touchstart', (e) => {
  e.preventDefault();
  const touch = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  startDraw({ offsetX: touch.clientX - rect.left, offsetY: touch.clientY - rect.top });
});
canvas.addEventListener('touchmove', (e) => {
  e.preventDefault();
  const touch = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  draw({ offsetX: touch.clientX - rect.left, offsetY: touch.clientY - rect.top });
});
canvas.addEventListener('touchend', stopDraw);

// --- Controls ---
clearBtn.addEventListener('click', () => {
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = 'black';
  history = [];
  // Save initial empty state
  history.push(canvas.toDataURL());
  undoBtn.disabled = true;       // <-- отключаем кнопку
  resultWrapper.style.display = 'none';
  // Revoke result URL too
  if (resultImg.src) {
    URL.revokeObjectURL(resultImg.src);
    resultImg.src = '';
  }
});

undoBtn.addEventListener('click', () => {
  if (history.length < 2) return;
  history.pop();
  const prev = history[history.length - 1];
  const img = new Image();
  img.onload = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);
  };
  img.src = prev;
  undoBtn.disabled = history.length <= 1;
});

// --- Submit ---
submitBtn.addEventListener('click', async () => {
  submitBtn.disabled = true;
  loading.style.display = 'block';
  resultWrapper.style.display = 'none';

  try {
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
    const formData = new FormData();
    formData.append('file', blob, 'sketch.png');

    const response = await fetch(`${SERVER_URL}/dorisuy`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    const imgBlob = await response.blob();
    // Revoke previous URL to prevent memory leak
    if (resultImg.src) {
      URL.revokeObjectURL(resultImg.src);
    }
    resultImg.src = URL.createObjectURL(imgBlob);
    resultWrapper.style.display = 'block';
  } catch (err) {
    alert('Ошибка: ' + err.message);
  } finally {
    submitBtn.disabled = false;
    loading.style.display = 'none';
  }
});
