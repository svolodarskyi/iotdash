import { rewriteGrafanaUrl } from '../lib/api'

interface GrafanaEmbedProps {
  url: string
  title: string
  refreshKey: number
}

export function GrafanaEmbed({ url, title, refreshKey }: GrafanaEmbedProps) {
  const browserUrl = rewriteGrafanaUrl(url)
  const fullUrl = `${browserUrl}&from=now-1h&to=now&refresh=5s&theme=light`

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-100">
        <h4 className="text-sm font-medium text-gray-700">{title}</h4>
      </div>
      <iframe
        key={refreshKey}
        src={fullUrl}
        title={title}
        width="100%"
        height="300"
        className="border-0"
      />
    </div>
  )
}
