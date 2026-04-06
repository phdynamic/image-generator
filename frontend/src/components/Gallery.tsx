import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Star, Image as ImageIcon } from 'lucide-react'
import { getImages, toggleFavorite, deleteImage } from '../lib/api'
import type { GeneratedImage } from '../lib/types'
import ImageCard from './ImageCard'
import ImageViewer from './ImageViewer'

export default function Gallery() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [viewingImage, setViewingImage] = useState<GeneratedImage | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['images', page, search, favoritesOnly],
    queryFn: () => getImages(page, 20, search || undefined, favoritesOnly || undefined),
  })

  const favoriteMutation = useMutation({
    mutationFn: toggleFavorite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteImage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] })
    },
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
    setPage(1)
  }

  const handleDelete = (id: number) => {
    if (confirm('Delete this image?')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="space-y-4">
      {/* Search and filters */}
      <div className="flex gap-3 items-center">
        <form onSubmit={handleSearch} className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search prompts..."
            className="w-full bg-slate-800 border border-slate-600 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
          />
        </form>
        <button
          onClick={() => {
            setFavoritesOnly(!favoritesOnly)
            setPage(1)
          }}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors border ${
            favoritesOnly
              ? 'bg-violet-600 border-violet-500 text-white'
              : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-white'
          }`}
        >
          <Star size={14} className={favoritesOnly ? 'fill-white' : ''} />
          Favorites
        </button>
      </div>

      {/* Image grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12 text-slate-400">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500" />
        </div>
      ) : data && data.images.length > 0 ? (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {data.images.map((image) => (
              <ImageCard
                key={image.id}
                image={image}
                onView={setViewingImage}
                onToggleFavorite={(id) => favoriteMutation.mutate(id)}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm text-white transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-slate-400">
                Page {data.page} of {data.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page >= data.pages}
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm text-white transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400">
          <ImageIcon size={48} className="mb-4 opacity-50" />
          <p className="text-lg">No images yet. Create your first one!</p>
        </div>
      )}

      {/* Image viewer modal */}
      {viewingImage && (
        <ImageViewer
          image={viewingImage}
          onClose={() => setViewingImage(null)}
          onToggleFavorite={(id) => favoriteMutation.mutate(id)}
          onDelete={handleDelete}
        />
      )}
    </div>
  )
}
