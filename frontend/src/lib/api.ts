import type { GenerateRequest, GeneratedImage, PaginatedImages, ModelInfo, GpuStatus } from './types'

const API_BASE = '/api'

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

  const response = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    body: formData,
  })
  return handleResponse<GeneratedImage>(response)
}

export async function upscaleImage(imageId: number, scale: number = 2): Promise<GeneratedImage> {
  const response = await fetch(`${API_BASE}/upscale/${imageId}?scale=${scale}`, {
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
  const response = await fetch(`${API_BASE}/images?${params}`)
  return handleResponse<PaginatedImages>(response)
}

export async function getImage(id: number): Promise<GeneratedImage> {
  const response = await fetch(`${API_BASE}/images/${id}`)
  return handleResponse<GeneratedImage>(response)
}

export async function deleteImage(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/images/${id}`, { method: 'DELETE' })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

export async function batchDeleteImages(ids: number[]): Promise<void> {
  const response = await fetch(`${API_BASE}/images/batch-delete`, {
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
  const response = await fetch(`${API_BASE}/images/${id}/favorite`, { method: 'POST' })
  return handleResponse<GeneratedImage>(response)
}

export async function getModels(): Promise<ModelInfo[]> {
  const response = await fetch(`${API_BASE}/models`)
  return handleResponse<ModelInfo[]>(response)
}

export async function getGpuStatus(): Promise<GpuStatus> {
  const response = await fetch(`${API_BASE}/gpu-status`)
  return handleResponse<GpuStatus>(response)
}

export async function getPromptHistory(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/prompts/history`)
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
  const response = await fetch(`${API_BASE}/templates`)
  return handleResponse<TemplateCategory[]>(response)
}

export async function enhancePrompt(prompt: string, style: string = 'general'): Promise<{ enhanced: string }> {
  const response = await fetch(`${API_BASE}/enhance-prompt`, {
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
