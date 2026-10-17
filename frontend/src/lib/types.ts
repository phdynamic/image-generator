export interface GeneratedImage {
  id: number
  prompt: string
  negative_prompt: string | null
  model_id: string
  seed: number
  steps: number
  cfg_scale: number
  width: number
  height: number
  file_path: string
  thumbnail_path: string | null
  generation_time: number | null
  is_favorite: boolean
  created_at: string
}

export interface GenerateRequest {
  prompt: string
  negative_prompt?: string
  model_id?: string
  seed?: number
  steps?: number
  cfg_scale?: number
  width?: number
  height?: number
  input_image?: File
  strength?: number
}

export interface PaginatedImages {
  images: GeneratedImage[]
  total: number
  page: number
  pages: number
}

export interface ModelInfo {
  id: string
  name: string
  type: string
  vram: string
  description: string
  is_loaded: boolean
  is_cached: boolean
  default_steps: number
  default_cfg: number
  default_size: number
  max_steps: number
  fixed_cfg: number | null
  supports_negative: boolean
  experimental: boolean
  gated: boolean
  needs_token: boolean
  download_gb: number | null
  download: DownloadState | null
}

export interface DownloadState {
  status: 'downloading' | 'error'
  downloaded_bytes: number
  total_bytes: number | null
  error: string | null
}

export interface GpuStatus {
  device: string
  name: string | null
  vram: { total: number; used: number; free: number } | null
  current_model: string | null
}

export interface AuthStatus {
  auth_required: boolean
  authenticated: boolean
}
