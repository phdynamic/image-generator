import { Heart, Trash2, Expand, CheckSquare } from 'lucide-react'
import type { GeneratedImage } from '../lib/types'
import { getThumbnailUrl, getImageUrl } from '../lib/api'

interface ImageCardProps {
  image: GeneratedImage
  onView?: (image: GeneratedImage) => void
  onToggleFavorite: (id: number) => void
  onDelete: (id: number) => void
  selectable?: boolean
  selected?: boolean
  onToggleSelect?: (id: number) => void
}

export default function ImageCard({ image, onView, onToggleFavorite, onDelete, selectable, selected, onToggleSelect }: ImageCardProps) {
  const imgSrc = image.thumbnail_path ? getThumbnailUrl(image) : getImageUrl(image)

  const handleClick = () => {
    if (selectable && onToggleSelect) {
      onToggleSelect(image.id)
    } else if (onView) {
      onView(image)
    }
  }

  return (
    <div
      className={`group relative bg-slate-800 rounded-xl overflow-hidden cursor-pointer border transition-all duration-200 hover:shadow-lg ${
        selected
          ? 'border-violet-500 ring-2 ring-violet-500/50 hover:shadow-violet-500/10'
          : 'border-slate-700 hover:border-violet-500/50 hover:shadow-violet-500/10'
      }`}
      onClick={handleClick}
    >
      <div className="aspect-square">
        <img
          src={imgSrc}
          alt={image.prompt}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      </div>

      {/* Selection checkbox */}
      {selectable && (
        <div className="absolute top-2 left-2 z-10">
          {selected
            ? <div className="w-6 h-6 rounded bg-violet-500 border-2 border-white flex items-center justify-center shadow-md shadow-black/50"><CheckSquare size={16} className="text-white" /></div>
            : <div className="w-6 h-6 rounded bg-black/40 border-2 border-white shadow-md shadow-black/50" />
          }
        </div>
      )}

      {/* Hover overlay */}
      {!selectable && (
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="absolute bottom-0 left-0 right-0 p-3">
            <p className="text-sm text-white line-clamp-2 mb-2">{image.prompt}</p>
            <div className="flex gap-2">
              <button
                onClick={(e) => { e.stopPropagation(); onToggleFavorite(image.id) }}
                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 transition-colors"
                title={image.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
              >
                <Heart size={16} className={image.is_favorite ? 'fill-red-500 text-red-500' : 'text-white'} />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onView?.(image) }}
                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 transition-colors"
                title="View full size"
              >
                <Expand size={16} className="text-white" />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(image.id) }}
                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-red-600 transition-colors"
                title="Delete image"
              >
                <Trash2 size={16} className="text-white" />
              </button>
            </div>
          </div>
        </div>
      )}

      {image.is_favorite && !selectable && (
        <div className="absolute top-2 right-2">
          <Heart size={16} className="fill-red-500 text-red-500 drop-shadow-lg" />
        </div>
      )}
    </div>
  )
}
