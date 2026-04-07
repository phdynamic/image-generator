import { useState, useRef, forwardRef, useImperativeHandle } from 'react'
import { Sparkles, ChevronDown, ChevronUp, Loader2, Upload, X } from 'lucide-react'
import type { GenerateRequest } from '../lib/types'

export interface PromptEditorHandle {
  setPrompt: (prompt: string) => void
}

interface PromptEditorProps {
  onGenerate: (request: GenerateRequest) => void
  isGenerating: boolean
  selectedModel?: string
}

const PromptEditor = forwardRef<PromptEditorHandle, PromptEditorProps>(({ onGenerate, isGenerating, selectedModel }, ref) => {
  const [prompt, setPrompt] = useState('')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [steps, setSteps] = useState(30)
  const [cfgScale, setCfgScale] = useState(7.5)
  const [width, setWidth] = useState(512)
  const [height, setHeight] = useState(512)
  const [seed, setSeed] = useState(-1)
  const [inputImage, setInputImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [strength, setStrength] = useState(0.75)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setInputImage(file)
      const reader = new FileReader()
      reader.onload = () => setImagePreview(reader.result as string)
      reader.readAsDataURL(file)
    }
  }

  const clearImage = () => {
    setInputImage(null)
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim() || isGenerating) return

    const request: GenerateRequest = {
      prompt: prompt.trim(),
      steps,
      cfg_scale: cfgScale,
      width,
      height,
    }
    if (negativePrompt.trim()) request.negative_prompt = negativePrompt.trim()
    if (selectedModel) request.model_id = selectedModel
    if (seed !== -1) request.seed = seed
    if (inputImage) {
      request.input_image = inputImage
      request.strength = strength
    }

    onGenerate(request)
  }

  useImperativeHandle(ref, () => ({
    setPrompt,
  }))

  const sizes = [256, 512, 768, 1024]

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to create..."
          rows={4}
          className="w-full bg-slate-800 border border-slate-600 rounded-xl p-4 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none text-lg"
        />
      </div>

      {/* Image-to-image upload */}
      <div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageSelect}
          className="hidden"
        />
        {imagePreview ? (
          <div className="relative bg-slate-800 border border-slate-600 rounded-xl p-3">
            <div className="flex items-start gap-3">
              <img src={imagePreview} alt="Input" className="w-20 h-20 object-cover rounded-lg" />
              <div className="flex-1">
                <p className="text-sm text-slate-300 mb-2">Image-to-Image mode</p>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">
                    Strength: {strength.toFixed(2)} <span className="text-slate-500">(higher = more change)</span>
                  </label>
                  <input
                    type="range"
                    min={0.1}
                    max={1}
                    step={0.05}
                    value={strength}
                    onChange={(e) => setStrength(Number(e.target.value))}
                    className="w-full accent-violet-500"
                  />
                </div>
              </div>
              <button
                type="button"
                onClick={clearImage}
                className="p-1 rounded-lg hover:bg-slate-700 transition-colors"
              >
                <X size={16} className="text-slate-400" />
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="w-full flex items-center justify-center gap-2 py-2.5 bg-slate-800/50 border border-dashed border-slate-600 rounded-xl text-sm text-slate-400 hover:text-white hover:border-violet-500/50 transition-colors"
          >
            <Upload size={16} />
            Upload image for img2img
          </button>
        )}
      </div>

      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
      >
        {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        Advanced Settings
      </button>

      {showAdvanced && (
        <div className="space-y-4 bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Negative Prompt</label>
            <textarea
              value={negativePrompt}
              onChange={(e) => setNegativePrompt(e.target.value)}
              placeholder="What to avoid in the image..."
              rows={2}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg p-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                Steps: {steps}
              </label>
              <input
                type="range"
                min={1}
                max={50}
                value={steps}
                onChange={(e) => setSteps(Number(e.target.value))}
                className="w-full accent-violet-500"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">
                CFG Scale: {cfgScale}
              </label>
              <input
                type="range"
                min={1}
                max={20}
                step={0.5}
                value={cfgScale}
                onChange={(e) => setCfgScale(Number(e.target.value))}
                className="w-full accent-violet-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Width</label>
              <select
                value={width}
                onChange={(e) => setWidth(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2 text-white focus:outline-none focus:ring-2 focus:ring-violet-500 text-sm"
              >
                {sizes.map((s) => (
                  <option key={s} value={s}>{s}px</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Height</label>
              <select
                value={height}
                onChange={(e) => setHeight(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2 text-white focus:outline-none focus:ring-2 focus:ring-violet-500 text-sm"
              >
                {sizes.map((s) => (
                  <option key={s} value={s}>{s}px</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Seed</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2 text-white focus:outline-none focus:ring-2 focus:ring-violet-500 text-sm"
                placeholder="-1 for random"
              />
            </div>
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={!prompt.trim() || isGenerating}
        className="w-full bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-semibold py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2 text-lg"
      >
        {isGenerating ? (
          <>
            <Loader2 size={20} className="animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Sparkles size={20} />
            {inputImage ? 'Generate (img2img)' : 'Generate'}
          </>
        )}
      </button>
    </form>
  )
})

PromptEditor.displayName = 'PromptEditor'

export default PromptEditor
