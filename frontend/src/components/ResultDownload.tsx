import { useState } from 'react'
import { runsApi } from '../api/client'

interface ResultDownloadProps {
  runId: string
}

export default function ResultDownload({ runId }: ResultDownloadProps) {
  const [isDownloading, setIsDownloading] = useState(false)

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const blob = await runsApi.export(runId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${runId}_export.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert('Failed to download export: ' + (err instanceof Error ? err.message : 'Unknown error'))
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="card">
      <h3 className="font-semibold mb-3">Export Results</h3>
      <button
        onClick={handleDownload}
        disabled={isDownloading}
        className="btn btn-primary w-full disabled:opacity-50"
      >
        {isDownloading ? 'Downloading...' : 'Download Complete Package (ZIP)'}
      </button>
      <p className="text-xs text-gray-500 mt-2">
        Includes all analysis results, geospatial data, and metadata
      </p>
    </div>
  )
}

