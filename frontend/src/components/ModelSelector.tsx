import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronDown, HardDrive, Download, Loader2, Trash2 } from 'lucide-react'
import { getModels, startModelDownload, deleteModel } from '../lib/api'
import type { ModelInfo } from '../lib/types'

interface ModelSelectorProps {
  value: string
  onChange: (modelId: string) => void
}

const GIB = 1024 ** 3
const gb = (bytes: number) => (bytes / GIB).toFixed(1)

export default function ModelSelector({ value, onChange }: ModelSelectorProps) {
  const queryClient = useQueryClient()

  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: getModels,
    // Keep the progress bar moving while anything is downloading.
    refetchInterval: (query) =>
      query.state.data?.some((m) => m.download?.status === 'downloading') ? 1500 : false,
  })

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['models'] })
  const downloadMutation = useMutation({ mutationFn: startModelDownload, onSettled: refresh })
  const deleteMutation = useMutation({ mutationFn: deleteModel, onSettled: refresh })

  if (isLoading) {
    return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-2 text-sm text-slate-400">
        Loading models...
      </div>
    )
  }

  if (!models || models.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-2 text-sm text-slate-400">
        No models available
      </div>
    )
  }

  const selected = models.find((m) => m.id === value)
  const busyModel = models.find((m) => m.download?.status === 'downloading')

  const handleDelete = (model: ModelInfo) => {
    const size = model.download_gb ? ` This frees about ${model.download_gb} GB.` : ''
    if (confirm(`Delete ${model.name} from this computer?${size} You can download it again later.`)) {
      deleteMutation.mutate(model.id)
    }
  }

  const mutationError = (downloadMutation.error ?? deleteMutation.error) as Error | null

  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1">Model</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => {
            downloadMutation.reset()
            deleteMutation.reset()
            onChange(e.target.value)
          }}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2.5 pr-10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent appearance-none"
        >
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.is_loaded ? '● ' : ''}{model.name} ({model.vram}){model.is_cached ? '' : ' ⤓'}
            </option>
          ))}
        </select>
        <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
      </div>

      {selected && (
        <div className="mt-1.5 space-y-2 text-xs text-slate-500">
          <p>{selected.description}</p>

          {selected.download?.status === 'downloading' ? (
            <DownloadProgress model={selected} />
          ) : selected.is_cached ? (
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5"><HardDrive size={12} /> Downloaded</span>
              <button
                onClick={() => handleDelete(selected)}
                disabled={deleteMutation.isPending}
                className="flex items-center gap-1 text-slate-500 hover:text-red-400 transition-colors disabled:opacity-50"
                title="Delete this model from the computer to free disk space"
              >
                <Trash2 size={12} /> Delete
              </button>
            </div>
          ) : (
            <button
              onClick={() => downloadMutation.mutate(selected.id)}
              disabled={!!busyModel || downloadMutation.isPending}
              title={busyModel ? `Wait for ${busyModel.name} to finish downloading` : undefined}
              className="w-full flex items-center justify-center gap-2 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm text-white transition-colors"
            >
              <Download size={14} />
              Download{selected.download_gb ? ` (~${selected.download_gb} GB)` : ''}
            </button>
          )}

          {selected.download?.status === 'error' && (
            <p className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-2">
              {selected.download.error}
            </p>
          )}
          {mutationError && (
            <p className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-2">
              {mutationError.message}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function DownloadProgress({ model }: { model: ModelInfo }) {
  const download = model.download!
  const known = download.total_bytes != null
  // Sizes are estimates, so never show "done" before the server says so.
  const percent = known ? Math.min(99, Math.round((download.downloaded_bytes / download.total_bytes!) * 100)) : null

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-slate-400">
        <span className="flex items-center gap-1.5">
          <Loader2 size={12} className="animate-spin" /> Downloading
        </span>
        <span>
          {gb(download.downloaded_bytes)} GB{known ? ` of ~${gb(download.total_bytes!)} GB` : ''}
        </span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
        <div
          className={`bg-violet-500 h-full rounded-full transition-all duration-500 ${percent == null ? 'animate-pulse w-full' : ''}`}
          style={percent == null ? undefined : { width: `${percent}%` }}
        />
      </div>
      <p>You can keep using other models while this downloads.</p>
    </div>
  )
}
