# Imaginaree — Implementation Plan

> A personal web app for AI image generation, built for instructional design work.
> Supports local GPU generation (NVIDIA 8GB) and free cloud API fallback.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React 18 + Vite + TypeScript | Fast dev experience, great component ecosystem |
| **UI Library** | Tailwind CSS + shadcn/ui | Beautiful, accessible components without heavy dependencies |
| **Backend** | Python 3.11 + FastAPI | Best ML/AI ecosystem, async support, WebSocket for live progress |
| **Task Queue** | Celery + Redis (or simple asyncio queue for v1) | Background job processing for generation tasks |
| **Database** | SQLite via SQLAlchemy | Zero config, perfect for personal tool, easy to back up |
| **Image Generation** | HuggingFace `diffusers` library | Unified API across all Stable Diffusion variants, FLUX, etc. |
| **Upscaling** | Real-ESRGAN | Best open-source upscaler, lightweight |
| **Cloud APIs** | HuggingFace Inference API (free tier) | Free fallback when local GPU is busy or for larger models |
| **WebSocket** | FastAPI WebSocket | Real-time generation progress (step previews, progress bars) |

---

## Models (Compatible with 8GB VRAM)

| Model | Type | VRAM | Speed | Quality | Best For |
|-------|------|------|-------|---------|----------|
| **Stable Diffusion 1.5** | text2img, img2img | ~4 GB | Fast | Good | Quick drafts, icons, patterns |
| **SDXL 1.0** | text2img, img2img | ~7 GB (fp16) | Medium | Great | High-quality illustrations, scenes |
| **FLUX.1-schnell** | text2img | ~8 GB (quantized) | Fast | Excellent | Best quality for complex prompts |
| **Real-ESRGAN x4** | upscale | ~1 GB | Fast | N/A | 4x upscaling any output |
| **ControlNet** (future) | guided generation | +2 GB | Slower | Great | Pose/edge-guided generation |

> **Note:** Models are loaded/unloaded on demand to stay within VRAM limits.
> Only one large model is active at a time.

---

## Project Structure

```
imaginaree/
├── frontend/                    # React + Vite app
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui base components
│   │   │   ├── PromptEditor.tsx # Main prompt input with options
│   │   │   ├── Gallery.tsx      # Image gallery grid
│   │   │   ├── ImageCard.tsx    # Single image with actions
│   │   │   ├── ModelSelector.tsx# Model picker dropdown
│   │   │   ├── ProgressBar.tsx  # Real-time generation progress
│   │   │   ├── ImageViewer.tsx  # Full-screen image view + details
│   │   │   ├── UpscaleDialog.tsx# Upscale options
│   │   │   └── Sidebar.tsx      # History / saved prompts
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts  # WebSocket connection for progress
│   │   │   └── useGeneration.ts # Generation API calls
│   │   ├── pages/
│   │   │   ├── Generate.tsx     # Main generation page
│   │   │   ├── Gallery.tsx      # Browse all generated images
│   │   │   └── Settings.tsx     # Model management, preferences
│   │   ├── lib/
│   │   │   ├── api.ts           # API client
│   │   │   └── types.ts         # Shared TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/                     # FastAPI Python app
│   ├── app/
│   │   ├── main.py              # FastAPI app entry, CORS, lifespan
│   │   ├── config.py            # Settings (model paths, DB, etc.)
│   │   ├── database.py          # SQLite setup via SQLAlchemy
│   │   ├── models/              # DB models
│   │   │   └── image.py         # Image record (prompt, params, path)
│   │   ├── routers/
│   │   │   ├── generate.py      # POST /generate (text2img, img2img)
│   │   │   ├── gallery.py       # GET /images, GET /images/:id
│   │   │   ├── upscale.py       # POST /upscale
│   │   │   ├── models.py        # GET /models, POST /models/load
│   │   │   └── websocket.py     # WS /ws/progress
│   │   ├── services/
│   │   │   ├── generator.py     # Core generation logic
│   │   │   ├── model_manager.py # Load/unload models, VRAM management
│   │   │   ├── upscaler.py      # Real-ESRGAN wrapper
│   │   │   ├── cloud_provider.py# HuggingFace Inference API client
│   │   │   └── prompt_enhancer.py # Optional: improve prompts for better results
│   │   └── utils/
│   │       ├── image_utils.py   # Save, resize, thumbnail generation
│   │       └── gpu_utils.py     # VRAM monitoring, device selection
│   ├── requirements.txt
│   └── pyproject.toml
│
├── outputs/                     # Generated images (gitignored)
│   ├── images/                  # Full-size outputs
│   └── thumbnails/              # Auto-generated thumbnails
│
├── models_cache/                # Downloaded model weights (gitignored)
├── .gitignore
├── README.md
└── PLAN.md                      # This file
```

---

## Phase 1 — Foundation (Core text-to-image)

**Goal:** Type a prompt, get an image, see it on screen.

### Backend
- [ ] Set up FastAPI project with CORS, static file serving
- [ ] Create SQLite database with `images` table (id, prompt, negative_prompt, model, seed, steps, cfg_scale, width, height, file_path, thumbnail_path, created_at)
- [ ] Implement `ModelManager` — downloads and loads Stable Diffusion 1.5 via `diffusers`
- [ ] Implement `POST /api/generate` endpoint:
  - Accepts: prompt, negative_prompt, model, seed, steps, cfg_scale, width, height
  - Runs generation on GPU
  - Saves image to `outputs/images/`
  - Creates thumbnail
  - Stores record in SQLite
  - Returns image metadata + URL
- [ ] Implement WebSocket `/ws/progress` for real-time step progress
- [ ] Implement `GET /api/images` (paginated list) and `GET /api/images/:id`
- [ ] Serve generated images via static file route

### Frontend
- [ ] Set up React + Vite + TypeScript + Tailwind project
- [ ] Build `PromptEditor` component: text area, negative prompt toggle, basic settings (steps, seed, size)
- [ ] Build `ProgressBar` with WebSocket connection showing generation progress
- [ ] Build basic `Gallery` grid showing generated images
- [ ] Build `ImageViewer` — click an image to see full-size + metadata (prompt, settings)
- [ ] Basic responsive layout with sidebar navigation

### Infrastructure
- [ ] Python virtual environment setup script
- [ ] `.gitignore` for outputs, model cache, node_modules, __pycache__
- [ ] Basic README with setup instructions

---

## Phase 2 — Multi-Model + Gallery

**Goal:** Switch between models, browse and manage your image history.

### Backend
- [ ] Expand `ModelManager` to support SDXL and FLUX.1-schnell
- [ ] VRAM-aware model swapping (unload current model before loading new one)
- [ ] `GET /api/models` — list available models with status (downloaded, loaded, available)
- [ ] `POST /api/models/:id/download` — trigger model download with progress
- [ ] Add search/filter to `GET /api/images` (by prompt text, model, date range)
- [ ] `DELETE /api/images/:id` — delete image + file
- [ ] `POST /api/images/:id/favorite` — toggle favorite flag

### Frontend
- [ ] `ModelSelector` dropdown showing available models with VRAM usage indicators
- [ ] Model download manager in Settings page (progress bars for downloads)
- [ ] Enhanced Gallery: search bar, filters (model, date, favorites), sort options
- [ ] Batch selection (select multiple images to delete or download)
- [ ] Prompt history sidebar — click to reuse previous prompts
- [ ] Image actions: download, copy prompt, delete, favorite

---

## Phase 3 — Cloud API Fallback

**Goal:** Generate images via free cloud APIs when local GPU is busy or for models too large for 8GB.

### Backend
- [ ] Implement `CloudProvider` for HuggingFace Inference API (free tier)
- [ ] Provider abstraction: `LocalProvider` and `CloudProvider` share same interface
- [ ] Auto-fallback: if local GPU is busy, offer cloud generation
- [ ] User choice: "Generate locally" vs "Generate in cloud" toggle
- [ ] API key management in settings (stored in local config file, not DB)

### Frontend
- [ ] Provider indicator on generate button (local GPU icon vs cloud icon)
- [ ] Settings page: API key input for HuggingFace
- [ ] Cloud model list (models available via API that are too large for local)

---

## Phase 4 — Image-to-Image + Upscaling

**Goal:** Use existing images as input, upscale outputs to print quality.

### Backend
- [ ] `POST /api/generate` — add img2img mode (accepts input image + strength parameter)
- [ ] Implement `Upscaler` service wrapping Real-ESRGAN
- [ ] `POST /api/upscale` — upscale an image by 2x or 4x
- [ ] Thumbnail regeneration after upscale

### Frontend
- [ ] Image upload zone in PromptEditor (drag & drop or file picker)
- [ ] img2img controls: strength slider (how much to change from original)
- [ ] "Upscale" button on any image in the gallery
- [ ] Side-by-side before/after comparison view for upscaled images

---

## Phase 5 — Polish + Instructional Design Features

**Goal:** Make it a joy to use for your daily instructional design work.

### Features
- [ ] **Prompt templates** — Pre-built prompts for common instructional design needs:
  - "Clean flat illustration of [subject] for e-learning course"
  - "Seamless tileable pattern with [theme]"
  - "Professional icon set: [items], consistent style"
  - "Realistic photo of [scenario] for training simulation"
  - "Decorative border/divider with [style] theme"
- [ ] **Prompt enhancer** — Optional AI-powered prompt improvement (append quality boosters, style keywords)
- [ ] **Collections** — Organize images into project folders (e.g., "Onboarding Course", "Safety Training")
- [ ] **Batch generation** — Generate multiple variations from one prompt (different seeds)
- [ ] **Image metadata export** — Copy/export prompt + settings for reproducibility
- [ ] **Quick re-generate** — "Generate similar" button that reuses settings with new seed
- [ ] **Dark/light theme** — because you'll be staring at this a lot

---

## API Overview

### REST Endpoints

```
POST   /api/generate              # Generate an image (text2img or img2img)
GET    /api/images                # List images (paginated, filterable)
GET    /api/images/:id            # Get single image details
DELETE /api/images/:id            # Delete an image
POST   /api/images/:id/favorite   # Toggle favorite
POST   /api/upscale               # Upscale an image
GET    /api/models                # List available models
POST   /api/models/:id/download   # Download a model
POST   /api/models/:id/load       # Load model into VRAM
GET    /api/settings              # Get app settings
PUT    /api/settings              # Update app settings
```

### WebSocket

```
WS /ws/progress    # Real-time generation progress (step count, preview images)
```

---

## Key Design Decisions

1. **One model at a time in VRAM** — With 8GB, we can't keep multiple large models loaded. The `ModelManager` handles loading/unloading gracefully with clear UI feedback.

2. **SQLite, not Postgres** — This is a personal tool. SQLite is fast, zero-config, and the entire DB is one file you can back up easily.

3. **Local-first, cloud-optional** — Local GPU is primary. Cloud APIs are a fallback, not a requirement. The app works fully offline.

4. **File-based image storage** — Images saved to `outputs/` directory, paths stored in DB. Simple, easy to browse outside the app, easy to back up.

5. **No authentication** — Personal tool running on localhost. No login needed.

6. **Async generation** — Generation runs in a background task. The UI stays responsive and shows progress via WebSocket. You can browse the gallery while an image generates.

---

## Setup Requirements

### System Requirements
- Python 3.11+
- Node.js 18+
- NVIDIA GPU with 8GB+ VRAM
- NVIDIA drivers + CUDA toolkit installed
- ~15 GB disk space for models (SD 1.5 ~4GB, SDXL ~7GB, FLUX ~8GB)

### Python Dependencies (key ones)
```
fastapi
uvicorn
sqlalchemy
diffusers
transformers
torch (CUDA build)
accelerate
safetensors
Pillow
realesrgan
websockets
python-multipart
```

### Node Dependencies (key ones)
```
react
react-dom
react-router-dom
@tanstack/react-query
tailwindcss
lucide-react (icons)
```

---

## Getting Started (will be refined during implementation)

```bash
# 1. Clone the repo
git clone <repo-url> && cd imaginaree

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 3. Frontend setup
cd ../frontend
npm install

# 4. Run both
# Terminal 1:
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2:
cd frontend && npm run dev
# Opens at http://localhost:5173
```

---

## Future Ideas (beyond v1)
- **ControlNet** — guide generation with edge maps, poses, depth maps
- **Inpainting** — paint over part of an image to regenerate just that area
- **LoRA support** — load fine-tuned style models (e.g., specific illustration styles)
- **Tiled generation** — create seamless patterns natively
- **SDXL Turbo / LCM** — near-instant generation (1-4 steps)
- **Mobile-friendly UI** — use from tablet while designing courses
- **Export presets** — save common size/quality combos (e.g., "Course header 1920x600")
