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
  const response = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return handleResponse<GeneratedImage>(response)
}

export async function getImages(
  page = 1,
  perPage = 20,
  search?: string,
  favoritesOnly?: boolean
): Promise<PaginatedImages> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  })
  if (search) params.set('search', search)
  if (favoritesOnly) params.set('favorites_only', 'true')
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

export function getImageUrl(image: GeneratedImage): string {
  return `/outputs/images/${image.file_path}`
}

export function getThumbnailUrl(image: GeneratedImage): string {
  return `/outputs/thumbnails/${image.thumbnail_path}`
}
