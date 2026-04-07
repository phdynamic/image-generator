import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Star, Image as ImageIcon, ArrowUpDown, CheckSquare, Square, Trash2, X } from 'lucide-react'
import { getImages, getModels, toggleFavorite, deleteImage, batchDeleteImages } from '../lib/api'
import type { GeneratedImage, GenerateRequest } from '../lib/types'
import ImageCard from './ImageCard'
import ImageViewer from './ImageViewer'

interface GalleryProps {
  onRegenerate?: (request: GenerateRequest) => void
}

export default function Gallery({ onRegenerate }: GalleryProps) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [sortBy, setSortBy] = useState('newest')
  const [modelFilter, setModelFilter] = useState('')
  const [viewingImage, setViewingImage] = useState<GeneratedImage | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [selectMode, setSelectMode] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['images', page, search, favoritesOnly, sortBy, modelFilter],
    queryFn: () => getImages(page, 20, search || undefined, favoritesOnly || undefined, sortBy, modelFilter || undefined),
  })

  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: getModels,
  })

  const favoriteMutation = useMutation({
    mutationFn: toggleFavorite,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['images'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteImage,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['images'] }),
  })

  const batchDeleteMutation = useMutation({
    mutationFn: batchDeleteImages,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] })
      setSelectedIds(new Set())
      setSelectMode(false)
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

  const handleBatchDelete = () => {
    if (selectedIds.size === 0) return
    if (confirm(`Delete ${selectedIds.size} selected images?`)) {
      batchDeleteMutation.mutate(Array.from(selectedIds))
    }
  }

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => {
    if (!data) return
    if (selectedIds.size === data.images.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(data.images.map(img => img.id)))
    }
  }

  return (
    <div className="space-y-4">
      {/* Search and filters */}
      <div>
        <label className="block text-sm text-slate-400 mb-1">Gallery</label>
        <div className="flex flex-wrap gap-3 items-center">
          <form onSubmit={handleSearch} className="flex-1 min-w-48 relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search prompts..."
              className="w-full bg-slate-800 border border-slate-600 rounded-lg pl-9 pr-3 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            />
          </form>

          <button
            onClick={() => { setFavoritesOnly(!favoritesOnly); setPage(1) }}
            className={`flex items-center gap-1.5 px-3 py-2.5 rounded-lg text-sm transition-colors border ${
              favoritesOnly
                ? 'bg-violet-600 border-violet-500 text-white'
                : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-white'
            }`}
          >
            <Star size={14} className={favoritesOnly ? 'fill-white' : ''} />
            Favorites
          </button>

          <button
            onClick={() => { setSelectMode(!selectMode); setSelectedIds(new Set()) }}
            className={`flex items-center gap-1.5 px-3 py-2.5 rounded-lg text-sm transition-colors border ${
              selectMode
                ? 'bg-violet-600 border-violet-500 text-white'
                : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-white'
            }`}
          >
            <CheckSquare size={14} />
            Select
          </button>
        </div>
      </div>

      {/* Sort and model filter row */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <ArrowUpDown size={14} className="text-slate-400" />
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
            className="bg-slate-800 border border-slate-600 rounded-lg px-2.5 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="model">By Model</option>
          </select>
        </div>

        {models && models.length > 0 && (
          <select
            value={modelFilter}
            onChange={(e) => { setModelFilter(e.target.value); setPage(1) }}
            className="bg-slate-800 border border-slate-600 rounded-lg px-2.5 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
          >
            <option value="">All Models</option>
            {models.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        )}

        {data && (
          <span className="text-xs text-slate-500 ml-auto">
            {data.total} image{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Batch actions bar */}
      {selectMode && (
        <div className="flex items-center gap-3 bg-slate-800/80 border border-slate-600 rounded-lg px-4 py-2">
          <button onClick={selectAll} className="flex items-center gap-1.5 text-sm text-slate-300 hover:text-white">
            {data && selectedIds.size === data.images.length ? <CheckSquare size={14} /> : <Square size={14} />}
            {data && selectedIds.size === data.images.length ? 'Deselect All' : 'Select All'}
          </button>
          <span className="text-sm text-slate-400">{selectedIds.size} selected</span>
          <div className="ml-auto flex gap-2">
            <button
              onClick={handleBatchDelete}
              disabled={selectedIds.size === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm text-white transition-colors"
            >
              <Trash2 size={14} />
              Delete ({selectedIds.size})
            </button>
            <button
              onClick={() => { setSelectMode(false); setSelectedIds(new Set()) }}
              className="p-1.5 rounded-lg hover:bg-slate-700 transition-colors"
            >
              <X size={16} className="text-slate-400" />
            </button>
          </div>
        </div>
      )}

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
                onView={selectMode ? undefined : setViewingImage}
                onToggleFavorite={(id) => favoriteMutation.mutate(id)}
                onDelete={handleDelete}
                selectable={selectMode}
                selected={selectedIds.has(image.id)}
                onToggleSelect={toggleSelect}
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
          onImageChanged={() => queryClient.invalidateQueries({ queryKey: ['images'] })}
          onRegenerate={onRegenerate}
        />
      )}
    </div>
  )
}
