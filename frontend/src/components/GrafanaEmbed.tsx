import { useState } from 'react'
import { rewriteGrafanaUrl } from '../lib/api'
import { useIsMobile } from '../hooks/useMediaQuery'

interface GrafanaEmbedProps {
  url: string
  title: string
  refreshKey: number
  lazyLoad?: boolean
}

export function GrafanaEmbed({ url, title, refreshKey, lazyLoad = false }: GrafanaEmbedProps) {
  const browserUrl = rewriteGrafanaUrl(url)
  const fullUrl = `${browserUrl}&from=now-1h&to=now&refresh=5s&theme=light`
  const isMobile = useIsMobile()
  const [loaded, setLoaded] = useState(!lazyLoad || !isMobile)
  const [isLoading, setIsLoading] = useState(true)

  // Responsive height: shorter on mobile, taller on desktop
  const height = isMobile ? 250 : 400

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-100">
        <h4 className="text-sm font-medium text-gray-700">{title}</h4>
      </div>

      {!loaded ? (
        // Lazy load button on mobile
        <div
          className="flex items-center justify-center bg-gray-50"
          style={{ height: `${height}px` }}
        >
          <button
            onClick={() => setLoaded(true)}
            className="px-6 py-3 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            Tap to load graph
          </button>
        </div>
      ) : (
        <div className="relative" style={{ height: `${height}px` }}>
          {/* Loading skeleton */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse delay-100" />
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse delay-200" />
              </div>
            </div>
          )}
          <iframe
            key={refreshKey}
            src={fullUrl}
            title={title}
            width="100%"
            height={height}
            className="border-0"
            onLoad={() => setIsLoading(false)}
          />
        </div>
      )}
    </div>
  )
}
