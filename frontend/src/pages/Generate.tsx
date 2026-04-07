import { useState, useRef } from 'react'
import PromptEditor, { type PromptEditorHandle } from '../components/PromptEditor'
import ModelSelector from '../components/ModelSelector'
import ProgressBar, { type ProgressBarHandle } from '../components/ProgressBar'
import PromptHistory from '../components/PromptHistory'
import PromptTemplates from '../components/PromptTemplates'
import Gallery from '../components/Gallery'
import { useGeneration } from '../hooks/useGeneration'
import type { GenerateRequest } from '../lib/types'

export default function Generate() {
  const [selectedModel, setSelectedModel] = useState('')
  const progressRef = useRef<ProgressBarHandle>(null)
  const promptEditorRef = useRef<PromptEditorHandle>(null)
  const { generate, isGenerating, error } = useGeneration(() => {
    progressRef.current?.clear()
  })

  const handleRegenerate = (request: GenerateRequest) => {
    generate(request)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left panel: controls */}
        <div className="w-full lg:w-96 flex-shrink-0 space-y-4">
          <ModelSelector value={selectedModel} onChange={setSelectedModel} />
          <PromptEditor
            ref={promptEditorRef}
            onGenerate={generate}
            isGenerating={isGenerating}
            selectedModel={selectedModel || undefined}
          />
          <ProgressBar ref={progressRef} isGenerating={isGenerating} />
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 text-sm">
              {error.message}
            </div>
          )}
          <PromptTemplates onSelectTemplate={(p) => promptEditorRef.current?.setPrompt(p)} />
          <PromptHistory onSelectPrompt={(p) => promptEditorRef.current?.setPrompt(p)} />
        </div>

        {/* Right panel: gallery */}
        <div className="flex-1 min-w-0">
          <Gallery onRegenerate={handleRegenerate} />
        </div>
      </div>
    </div>
  )
}
