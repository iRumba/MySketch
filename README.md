# MySketch ✏️✨

AI sketch completion — нарисуй набросок, а нейросеть дорисует его.

## Как это работает

1. Пользователь рисует чёрным карандашом на холсте
2. Нажимает «Дорисуй»
3. Изображение отправляется в **Fooocus** (SDXL + ControlNet)
4. AI дорисовывает детали, сохраняя форму наброска
5. Результат показывается на экране

## Быстрый старт

### 1. Запусти Fooocus (Colab)

Открой `colab/fooocus_colab.ipynb` в Google Colab и запусти все ячейки.
После запуска появится публичный URL (например, `https://xxxx.gradio.live`).

### 2. Запусти прокси-сервер

```bash
cd server
pip install -r requirements.txt
set FOOOCUS_URL=https://xxxx.gradio.live
python server.py
```

### 3. Открой клиент

Открой `client/index.html` в браузере и рисуй!

## Технологии

- **Клиент:** HTML5 Canvas, Vanilla JS
- **Сервер:** Python FastAPI
- **Генерация:** SDXL + ControlNet (Fooocus)

## Структура проекта

```
MySketch/
├── client/          # Frontend (холст + кнопка)
│   ├── index.html
│   ├── script.js
│   └── style.css
├── server/          # Backend (прокси к Fooocus)
│   ├── server.py
│   └── requirements.txt
├── colab/           # Colab ноутбук
│   └── fooocus_colab.ipynb
├── docs/            # Документация
│   └── technical/
│       ├── architecture.md
│       └── requirements.md
├── .gitignore
└── README.md
```

## Документация

Подробнее — в [docs/](docs/README.md)
