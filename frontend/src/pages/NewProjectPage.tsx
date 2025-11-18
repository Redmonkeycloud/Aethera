import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { projectsApi } from '../api/client'

export default function NewProjectPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [country, setCountry] = useState('')
  const [sector, setSector] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError('Project name is required')
      return
    }

    setIsSubmitting(true)

    try {
      const project = await projectsApi.create({
        name: name.trim(),
        country: country || undefined,
        sector: sector || undefined,
      })
      navigate(`/projects/${project.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Create New Project</h1>

      <form onSubmit={handleSubmit} className="card space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Project Name <span className="text-red-500">*</span>
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input"
            placeholder="Enter project name"
            required
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">
            Country
          </label>
          <select
            id="country"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="input"
            disabled={isSubmitting}
          >
            <option value="">Select country...</option>
            <option value="DEU">Germany</option>
            <option value="FRA">France</option>
            <option value="ITA">Italy</option>
            <option value="GRC">Greece</option>
          </select>
        </div>

        <div>
          <label htmlFor="sector" className="block text-sm font-medium text-gray-700 mb-1">
            Sector
          </label>
          <select
            id="sector"
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="input"
            disabled={isSubmitting}
          >
            <option value="">Select sector...</option>
            <option value="renewable-energy">Renewable Energy</option>
            <option value="infrastructure">Infrastructure</option>
            <option value="mining">Mining</option>
            <option value="agriculture">Agriculture</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="flex space-x-4">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn btn-secondary flex-1"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !name.trim()}
            className="btn btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </form>
    </div>
  )
}

