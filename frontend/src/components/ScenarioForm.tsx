import { useState } from 'react'
import { useAppStore } from '../store/useAppStore'
import { runsApi, RunCreate } from '../api/client'

interface ScenarioFormProps {
  projectId: string
  onRunCreated: (taskId: string) => void
}

export default function ScenarioForm({ projectId, onRunCreated }: ScenarioFormProps) {
  const { aoiGeometry } = useAppStore()
  const [projectType, setProjectType] = useState('solar')
  const [country, setCountry] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!aoiGeometry) {
      setError('Please draw or upload an AOI first')
      return
    }

    setIsSubmitting(true)

    try {
      const runData: RunCreate = {
        aoi_geojson: aoiGeometry,
        project_type: projectType,
        country: country || undefined,
      }

      const response = await runsApi.create(projectId, runData)
      onRunCreated(response.task_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card space-y-4">
      <h2 className="text-xl font-semibold">Create Analysis Run</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Project Type
        </label>
        <select
          value={projectType}
          onChange={(e) => setProjectType(e.target.value)}
          className="input"
          required
        >
          <option value="solar">Solar</option>
          <option value="wind">Wind</option>
          <option value="hydro">Hydro</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Country (Optional)
        </label>
        <select
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          className="input"
        >
          <option value="">Select country...</option>
          <option value="DEU">Germany</option>
          <option value="FRA">France</option>
          <option value="ITA">Italy</option>
          <option value="GRC">Greece</option>
        </select>
      </div>

      <div className="text-sm text-gray-600">
        {aoiGeometry ? (
          <span className="text-green-600">✓ AOI defined</span>
        ) : (
          <span className="text-amber-600">⚠ Please draw or upload an AOI</span>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting || !aoiGeometry}
        className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting ? 'Creating...' : 'Start Analysis'}
      </button>
    </form>
  )
}

