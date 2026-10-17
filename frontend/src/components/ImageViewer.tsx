import { useEffect, useCallback, useRef, useState } from 'react'
import { X, Download, Heart, Trash2, Copy, Send, ZoomIn, Loader2, RefreshCw } from 'lucide-react'
import type { GeneratedImage, GenerateRequest } from '../lib/types'
import { getImageUrl, upscaleImage } from '../lib/api'

interface ImageViewerProps {
  image: GeneratedImage
  onClose: () => void
  onToggleFavorite: (id: number) => void
  onDelete: (id: number) => void
  onImageChanged?: () => void
  onRegenerate?: (request: GenerateRequest) => void
}

export default function ImageViewer({ image, onClose, onToggleFavorite, onDelete, onImageChanged, onRegenerate }: ImageViewerProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    },
    [onClose]
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [handleKeyDown])

  // On a phone, Back should close the viewer rather than leave the app. Opening adds
  // a history entry; Back (or any other way of closing) removes it again.
  const closeRef = useRef(onClose)
  closeRef.current = onClose
  useEffect(() => {
    let entryPending = true
    window.history.pushState({ imaginareeViewer: true }, '')
    const onPop = () => {
      entryPending = false
      closeRef.current()
    }
    window.addEventListener('popstate', onPop)
    return () => {
      window.removeEventListener('popstate', onPop)
      if (entryPending) window.history.back()
    }
  }, [])

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose()
  }

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = getImageUrl(image)
    link.download = `imaginaree-${image.id}.png`
    link.click()
  }

  const handleCopyPrompt = async () => {
    await navigator.clipboard.writeText(image.prompt)
  }

  const handleDelete = () => {
    onDelete(image.id)
    onClose()
  }

  const [stashlyStatus, setStashlyStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [stashlyError, setStashlyError] = useState('')

  const handleSendToStashly = async () => {
    setStashlyStatus('sending')
    try {
      const imageUrl = `${window.location.origin}${getImageUrl(image)}`
      const res = await fetch('http://127.0.0.1:9473/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: imageUrl,
          title: image.prompt.length > 60 ? image.prompt.substring(0, 60) + '...' : image.prompt,
          description: image.prompt,
          tags: image.prompt.toLowerCase().split(/[\s,]+/).filter(w => w.length > 3).slice(0, 8),
          source: `Imaginaree (${image.model_id})`,
          photographer: '',
          contentType: 'aiart',
        }),
      })
      if (res.ok) {
        setStashlyStatus('sent')
        setTimeout(() => setStashlyStatus('idle'), 2000)
      } else {
        const err = await res.json()
        throw new Error(err.error || 'Failed')
      }
    } catch (e: any) {
      setStashlyStatus('error')
      setStashlyError(e.message === 'Failed to fetch' ? 'Stashly not running' : e.message)
      setTimeout(() => setStashlyStatus('idle'), 3000)
    }
  }

  const [upscaleStatus, setUpscaleStatus] = useState<'idle' | 'upscaling' | 'done' | 'error'>('idle')

  const handleUpscale = async (scale: number) => {
    setUpscaleStatus('upscaling')
    try {
      await upscaleImage(image.id, scale)
      setUpscaleStatus('done')
      onImageChanged?.()
      setTimeout(() => setUpscaleStatus('idle'), 2000)
    } catch {
      setUpscaleStatus('error')
      setTimeout(() => setUpscaleStatus('idle'), 3000)
    }
  }

  const handleRegenerate = () => {
    if (!onRegenerate) return
    onRegenerate({
      prompt: image.prompt,
      negative_prompt: image.negative_prompt || undefined,
      model_id: image.model_id,
      steps: image.steps,
      cfg_scale: image.cfg_scale,
      width: image.width,
      height: image.height,
    })
    onClose()
  }

  const createdDate = new Date(image.created_at).toLocaleString()

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm md:flex md:items-center md:justify-center md:p-4"
      onClick={handleBackdropClick}
    >
      {/* Phones: one full-screen page that scrolls. Desktop: picture beside the details. */}
      <div className="bg-slate-800 w-full h-dvh overflow-y-auto overscroll-contain flex flex-col md:flex-row md:h-auto md:max-h-[90vh] md:max-w-6xl md:overflow-hidden md:rounded-2xl md:border md:border-slate-700 md:shadow-2xl">
        {/* Image section */}
        <div className="shrink-0 md:shrink md:flex-1 md:min-h-0 bg-slate-900 flex items-center justify-center p-3 md:p-4">
          <img
            src={getImageUrl(image)}
            alt={image.prompt}
            className="max-w-full max-h-[60dvh] md:max-h-[70vh] object-contain rounded-lg"
          />
        </div>

        {/* Metadata sidebar */}
        <div className="w-full md:w-96 shrink-0 flex flex-col border-t md:border-t-0 md:border-l border-slate-700">
          <div className="flex items-center justify-between p-4 border-b border-slate-700">
            <h3 className="text-lg font-semibold text-white">Details</h3>
            <button
              onClick={onClose}
              aria-label="Close"
              className="hidden md:block p-1.5 rounded-lg hover:bg-slate-700 transition-colors"
            >
              <X size={20} className="text-slate-400" />
            </button>
          </div>

          <div className="p-4 space-y-4 md:flex-1 md:overflow-y-auto">
            <div>
              <label className="text-xs text-slate-400 uppercase tracking-wider">Prompt</label>
              <p className="text-sm text-white mt-1">{image.prompt}</p>
            </div>

            {image.negative_prompt && (
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wider">
                  Negative Prompt
                </label>
                <p className="text-sm text-slate-300 mt-1">{image.negative_prompt}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wider">Model</label>
                <p className="text-sm text-white mt-1">{image.model_id}</p>
              </div>
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wider">Seed</label>
                <p className="text-sm text-white mt-1">{image.seed}</p>
              </div>
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wider">Steps</label>
                <p className="text-sm text-white mt-1">{image.steps}</p>
              </div>
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wider">CFG Scale</label>
                <p className="text-sm text-white mt-1">{image.cfg_scale}</p>
              </div>
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wider">Dimensions</label>
                <p className="text-sm text-white mt-1">
                  {image.width} x {image.height}
                </p>
              </div>
              {image.generation_time != null && (
                <div>
                  <label className="text-xs text-slate-400 uppercase tracking-wider">
                    Gen. Time
                  </label>
                  <p className="text-sm text-white mt-1">{image.generation_time.toFixed(1)}s</p>
                </div>
              )}
            </div>

            <div>
              <label className="text-xs text-slate-400 uppercase tracking-wider">Created</label>
              <p className="text-sm text-white mt-1">{createdDate}</p>
            </div>
          </div>

          {/* Actions */}
          <div className="sticky bottom-0 md:static bg-slate-800 p-4 pb-[max(1rem,env(safe-area-inset-bottom))] border-t border-slate-700 flex flex-wrap gap-2">
            {onRegenerate && (
              <button
                onClick={handleRegenerate}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-violet-600 hover:bg-violet-500 rounded-lg transition-colors text-sm text-white"
                title="Generate similar with new seed"
              >
                <RefreshCw size={16} />
                Regen
              </button>
            )}
            <button
              onClick={handleDownload}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-sm text-white"
              title="Download"
            >
              <Download size={16} />
              Save
            </button>
            <button
              onClick={handleCopyPrompt}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-sm text-white"
              title="Copy prompt"
            >
              <Copy size={16} />
              Copy
            </button>
            <button
              onClick={handleSendToStashly}
              disabled={stashlyStatus === 'sending'}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg transition-colors text-sm ${
                stashlyStatus === 'sent'
                  ? 'bg-emerald-700 text-white'
                  : stashlyStatus === 'error'
                  ? 'bg-red-700 text-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-white'
              }`}
              title="Send to Stashly"
            >
              <Send size={16} />
              {stashlyStatus === 'sending' ? '...' : stashlyStatus === 'sent' ? 'Sent!' : stashlyStatus === 'error' ? stashlyError : 'Stash'}
            </button>
            <button
              onClick={() => handleUpscale(2)}
              disabled={upscaleStatus === 'upscaling'}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg transition-colors text-sm ${
                upscaleStatus === 'done'
                  ? 'bg-emerald-700 text-white'
                  : upscaleStatus === 'error'
                  ? 'bg-red-700 text-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-white'
              }`}
              title="Upscale image 2x"
            >
              {upscaleStatus === 'upscaling' ? <Loader2 size={16} className="animate-spin" /> : <ZoomIn size={16} />}
              {upscaleStatus === 'done' ? 'Done!' : upscaleStatus === 'error' ? 'Error' : '2x'}
            </button>
            <button
              onClick={() => onToggleFavorite(image.id)}
              className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
              title={image.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              <Heart
                size={16}
                className={image.is_favorite ? 'fill-red-500 text-red-500' : 'text-white'}
              />
            </button>
            <button
              onClick={handleDelete}
              className="p-2 bg-slate-700 hover:bg-red-600 rounded-lg transition-colors"
              title="Delete image"
            >
              <Trash2 size={16} className="text-white" />
            </button>
          </div>
        </div>
      </div>

      {/* Phones: a large close button that stays on screen however far you scroll */}
      <button
        onClick={onClose}
        aria-label="Close"
        className="md:hidden fixed right-3 top-[max(0.75rem,env(safe-area-inset-top))] z-10 w-11 h-11 rounded-full bg-black/70 backdrop-blur flex items-center justify-center shadow-lg"
      >
        <X size={22} className="text-white" />
      </button>
    </div>
  )
}
