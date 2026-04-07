import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { generateImage } from '../lib/api'
import type { GenerateRequest } from '../lib/types'

export function useGeneration(onComplete?: () => void) {
  const queryClient = useQueryClient()
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const generate = async (requests: GenerateRequest | GenerateRequest[]) => {
    const batch = Array.isArray(requests) ? requests : [requests]
    setIsGenerating(true)
    setError(null)

    for (const request of batch) {
      try {
        await generateImage(request)
        queryClient.invalidateQueries({ queryKey: ['images'] })
      } catch (e) {
        setError(e instanceof Error ? e : new Error(String(e)))
        break
      }
    }

    setIsGenerating(false)
    onComplete?.()
  }

  return {
    generate,
    isGenerating,
    error,
  }
}
