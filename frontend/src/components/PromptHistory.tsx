import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Clock, ChevronDown, ChevronUp } from 'lucide-react'
import { getPromptHistory } from '../lib/api'

interface PromptHistoryProps {
  onSelectPrompt: (prompt: string) => void
}

export default function PromptHistory({ onSelectPrompt }: PromptHistoryProps) {
  const [expanded, setExpanded] = useState(false)

  const { data: prompts } = useQuery({
    queryKey: ['prompt-history'],
    queryFn: getPromptHistory,
  })

  if (!prompts || prompts.length === 0) return null

  const displayed = expanded ? prompts : prompts.slice(0, 5)

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-3">
      <div className="flex items-center gap-2 mb-2">
        <Clock size={14} className="text-slate-400" />
        <span className="text-sm font-medium text-slate-300">Recent Prompts</span>
      </div>
      <div className="space-y-1">
        {displayed.map((prompt, i) => (
          <button
            key={i}
            onClick={() => onSelectPrompt(prompt)}
            className="w-full text-left text-xs text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg px-2 py-1.5 transition-colors line-clamp-2"
            title={prompt}
          >
            {prompt}
          </button>
        ))}
      </div>
      {prompts.length > 5 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 mt-2 text-xs text-violet-400 hover:text-violet-300"
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? 'Show less' : `Show all (${prompts.length})`}
        </button>
      )}
    </div>
  )
}
