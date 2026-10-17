import type { GenerateRequest, GeneratedImage, PaginatedImages, ModelInfo, GpuStatus, AuthStatus } from './types'

const API_BASE = '/api'

/** Fired whenever the server says the session has ended, so the app can show the sign-in page. */
export const UNAUTHORIZED_EVENT = 'imaginaree:unauthorized'

async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(input, init)
  if (response.status === 401) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
  return response
}

export async function getAuthStatus(): Promise<AuthStatus> {
  const response = await fetch(`${API_BASE}/auth/status`)
  return handleResponse<AuthStatus>(response)
}

export async function login(password: string): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  })
  await handleResponse<unknown>(response)
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE}/auth/logout`, { method: 'POST' })
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function generateImage(request: GenerateRequest): Promise<GeneratedImage> {
  const formData = new FormData()
  formData.append('prompt', request.prompt)
  if (request.negative_prompt) formData.append('negative_prompt', request.negative_prompt)
  if (request.model_id) formData.append('model_id', request.model_id)
  if (request.seed !== undefined) formData.append('seed', String(request.seed))
  if (request.steps !== undefined) formData.append('steps', String(request.steps))
  if (request.cfg_scale !== undefined) formData.append('cfg_scale', String(request.cfg_scale))
  if (request.width !== undefined) formData.append('width', String(request.width))
  if (request.height !== undefined) formData.append('height', String(request.height))
  if (request.strength !== undefined) formData.append('strength', String(request.strength))
  if (request.input_image) formData.append('input_image', request.input_image)

  const response = await apiFetch(`${API_BASE}/generate`, {
    method: 'POST',
    body: formData,
  })
  const { job_id } = await handleResponse<{ job_id: string }>(response)
  return waitForJob(job_id)
}

interface JobStatus {
  status: 'queued' | 'running' | 'done' | 'error'
  image: GeneratedImage | null
  error: string | null
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

/**
 * Generation runs as a background job on the server: long requests get cut off
 * by proxies, so we poll instead of waiting on one request.
 */
async function waitForJob(jobId: string): Promise<GeneratedImage> {
  let failures = 0
  for (;;) {
    await sleep(1000)
    let job: JobStatus
    try {
      const response = await apiFetch(`${API_BASE}/jobs/${jobId}`)
      job = await handleResponse<JobStatus>(response)
      failures = 0
    } catch (err) {
      // A dropped connection shouldn't lose the image; only give up after a while.
      if (++failures >= 15) throw err
      continue
    }
    if (job.status === 'done' && job.image) return job.image
    if (job.status === 'error') throw new Error(job.error || 'Image generation failed')
  }
}

export async function upscaleImage(imageId: number, scale: number = 2): Promise<GeneratedImage> {
  const response = await apiFetch(`${API_BASE}/upscale/${imageId}?scale=${scale}`, {
    method: 'POST',
  })
  return handleResponse<GeneratedImage>(response)
}

export async function getImages(
  page = 1,
  perPage = 20,
  search?: string,
  favoritesOnly?: boolean,
  sortBy?: string,
  modelFilter?: string,
): Promise<PaginatedImages> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  })
  if (search) params.set('search', search)
  if (favoritesOnly) params.set('favorites_only', 'true')
  if (sortBy) params.set('sort_by', sortBy)
  if (modelFilter) params.set('model_filter', modelFilter)
  const response = await apiFetch(`${API_BASE}/images?${params}`)
  return handleResponse<PaginatedImages>(response)
}

export async function getImage(id: number): Promise<GeneratedImage> {
  const response = await apiFetch(`${API_BASE}/images/${id}`)
  return handleResponse<GeneratedImage>(response)
}

export async function deleteImage(id: number): Promise<void> {
  const response = await apiFetch(`${API_BASE}/images/${id}`, { method: 'DELETE' })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

export async function batchDeleteImages(ids: number[]): Promise<void> {
  const response = await apiFetch(`${API_BASE}/images/batch-delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

export async function toggleFavorite(id: number): Promise<GeneratedImage> {
  const response = await apiFetch(`${API_BASE}/images/${id}/favorite`, { method: 'POST' })
  return handleResponse<GeneratedImage>(response)
}

export async function getModels(): Promise<ModelInfo[]> {
  const response = await apiFetch(`${API_BASE}/models`)
  return handleResponse<ModelInfo[]>(response)
}

export async function getGpuStatus(): Promise<GpuStatus> {
  const response = await apiFetch(`${API_BASE}/gpu-status`)
  return handleResponse<GpuStatus>(response)
}

export async function getPromptHistory(): Promise<string[]> {
  const response = await apiFetch(`${API_BASE}/prompts/history`)
  return handleResponse<string[]>(response)
}

export interface PromptTemplate {
  name: string
  prompt: string
  placeholder: string
}

export interface TemplateCategory {
  category: string
  templates: PromptTemplate[]
}

export async function getTemplates(): Promise<TemplateCategory[]> {
  const response = await apiFetch(`${API_BASE}/templates`)
  return handleResponse<TemplateCategory[]>(response)
}

export async function enhancePrompt(prompt: string, style: string = 'general'): Promise<{ enhanced: string }> {
  const response = await apiFetch(`${API_BASE}/enhance-prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, style }),
  })
  return handleResponse<{ enhanced: string }>(response)
}

export function getImageUrl(image: GeneratedImage): string {
  return `/outputs/images/${image.file_path}`
}

export function getThumbnailUrl(image: GeneratedImage): string {
  return `/outputs/thumbnails/${image.thumbnail_path}`
}
