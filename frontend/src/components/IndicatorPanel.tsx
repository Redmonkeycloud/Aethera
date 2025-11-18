import { RunDetail } from '../api/client'

interface IndicatorPanelProps {
  run: RunDetail
  results?: Record<string, unknown>
}

export default function IndicatorPanel({ run, results }: IndicatorPanelProps) {
  const formatValue = (value: unknown): string => {
    if (typeof value === 'number') {
      return value.toFixed(2)
    }
    return String(value ?? 'N/A')
  }

  return (
    <div className="card space-y-4">
      <h2 className="text-xl font-semibold">Environmental Indicators</h2>

      {results?.kpis && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-700">Key Performance Indicators</h3>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(results.kpis as Record<string, unknown>).map(([key, value]) => (
              <div key={key} className="bg-gray-50 p-3 rounded">
                <div className="text-xs text-gray-500 uppercase tracking-wide">{key}</div>
                <div className="text-lg font-semibold text-gray-900">{formatValue(value)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {results?.biodiversity && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-700">Biodiversity</h3>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Score</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatValue((results.biodiversity as { score?: number })?.score)}
            </div>
          </div>
        </div>
      )}

      {results?.emissions && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-700">Emissions</h3>
          <div className="space-y-2">
            {Object.entries(results.emissions as Record<string, unknown>).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-sm text-gray-600">{key}</span>
                <span className="text-sm font-medium">{formatValue(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {results?.resm && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-700">RESM Score</h3>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-lg font-semibold text-gray-900">
              {formatValue((results.resm as { score?: number })?.score)}
            </div>
          </div>
        </div>
      )}

      {results?.ahsm && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-700">AHSM Score</h3>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-lg font-semibold text-gray-900">
              {formatValue((results.ahsm as { score?: number })?.score)}
            </div>
          </div>
        </div>
      )}

      {results?.cim && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-700">CIM Score</h3>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-lg font-semibold text-gray-900">
              {formatValue((results.cim as { score?: number })?.score)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

