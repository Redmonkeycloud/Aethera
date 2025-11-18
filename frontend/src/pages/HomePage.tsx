import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { projectsApi, type Project } from '../api/client'
import { format } from 'date-fns'

export default function HomePage() {
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
    retry: 1,
    retryDelay: 1000,
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
        <Link
          to="/projects/new"
          className="btn btn-primary"
        >
          New Project
        </Link>
      </div>

      {error ? (
        <div className="text-center py-12">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Projects</h2>
            <p className="text-red-600 text-sm mb-4">
              {error instanceof Error ? error.message : 'Failed to connect to the API'}
            </p>
            <p className="text-gray-600 text-xs">
              Make sure the backend API is running at http://localhost:8000
            </p>
          </div>
        </div>
      ) : isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading projects...</p>
        </div>
      ) : projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project: Project) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="card hover:shadow-md transition-shadow"
            >
              <h2 className="text-xl font-semibold mb-2">{project.name}</h2>
              <div className="space-y-1 text-sm text-gray-600">
                {project.country && (
                  <div>
                    <span className="font-medium">Country:</span> {project.country}
                  </div>
                )}
                {project.sector && (
                  <div>
                    <span className="font-medium">Sector:</span> {project.sector}
                  </div>
                )}
                <div>
                  <span className="font-medium">Created:</span>{' '}
                  {format(new Date(project.created_at), 'PPp')}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">No projects yet</p>
          <Link to="/projects/new" className="btn btn-primary">
            Create Your First Project
          </Link>
        </div>
      )}
    </div>
  )
}

