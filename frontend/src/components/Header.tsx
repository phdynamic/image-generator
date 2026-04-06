import { Sparkles, Cloud } from 'lucide-react'

export default function Header() {
  return (
    <header className="bg-slate-800/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles size={24} className="text-violet-400" />
          <h1 className="text-xl font-bold text-white tracking-tight">Imaginaree</h1>
        </div>

        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Cloud size={16} />
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span>HuggingFace API</span>
        </div>
      </div>
    </header>
  )
}
