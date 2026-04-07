import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import { getTemplates } from '../lib/api'

interface PromptTemplatesProps {
  onSelectTemplate: (prompt: string) => void
}

export default function PromptTemplates({ onSelectTemplate }: PromptTemplatesProps) {
  const [expanded, setExpanded] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  const { data: categories } = useQuery({
    queryKey: ['templates'],
    queryFn: getTemplates,
  })

  if (!categories) return null

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 w-full"
      >
        <BookOpen size={14} className="text-violet-400" />
        <span className="text-sm font-medium text-slate-300">Prompt Templates</span>
        <span className="ml-auto">
          {expanded ? <ChevronUp size={14} className="text-slate-400" /> : <ChevronDown size={14} className="text-slate-400" />}
        </span>
      </button>

      {expanded && (
        <div className="mt-3 space-y-2">
          {/* Category tabs */}
          <div className="flex flex-wrap gap-1.5">
            {categories.map((cat) => (
              <button
                key={cat.category}
                onClick={() => setActiveCategory(activeCategory === cat.category ? null : cat.category)}
                className={`px-2.5 py-1 rounded-lg text-xs transition-colors ${
                  activeCategory === cat.category
                    ? 'bg-violet-600 text-white'
                    : 'bg-slate-700/50 text-slate-400 hover:text-white'
                }`}
              >
                {cat.category}
              </button>
            ))}
          </div>

          {/* Templates for active category */}
          {activeCategory && (
            <div className="space-y-1.5 pt-1">
              {categories
                .find((c) => c.category === activeCategory)
                ?.templates.map((t) => (
                  <button
                    key={t.name}
                    onClick={() => onSelectTemplate(t.prompt.replace('{subject}', t.placeholder))}
                    className="w-full text-left bg-slate-700/30 hover:bg-slate-700/60 rounded-lg px-3 py-2 transition-colors"
                  >
                    <p className="text-xs font-medium text-slate-300">{t.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
                      {t.prompt.replace('{subject}', t.placeholder)}
                    </p>
                  </button>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
