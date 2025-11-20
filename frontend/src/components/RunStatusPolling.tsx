import { useEffect, useState } from 'react'
import { tasksApi, TaskStatus } from '../api/client'

interface RunStatusPollingProps {
  taskId: string
  onComplete: (runId: string) => void
  onError: (error: string) => void
}

export default function RunStatusPolling({
  taskId,
  onComplete,
  onError,
}: RunStatusPollingProps) {
  const [status, setStatus] = useState<TaskStatus | null>(null)
  const [isPolling, setIsPolling] = useState(true)

  useEffect(() => {
    if (!isPolling) return

    const pollInterval = setInterval(async () => {
      try {
        const taskStatus = await tasksApi.getStatus(taskId)
        setStatus(taskStatus)

        if (taskStatus.status === 'COMPLETED') {
          setIsPolling(false)
          if (taskStatus.run_id) {
            onComplete(taskStatus.run_id)
          }
        } else if (taskStatus.status === 'FAILED') {
          setIsPolling(false)
          onError(taskStatus.error || 'Task failed')
        }
      } catch (err) {
        setIsPolling(false)
        onError(err instanceof Error ? err.message : 'Failed to get task status')
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(pollInterval)
  }, [taskId, isPolling, onComplete, onError])

  if (!status) {
    return (
      <div className="card">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
          <span className="text-gray-600">Checking status...</span>
        </div>
      </div>
    )
  }

  const statusColors: Record<string, string> = {
    PENDING: 'bg-yellow-100 text-yellow-800',
    PROCESSING: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">Run Status</h3>
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${
            statusColors[status.status] || 'bg-gray-100 text-gray-800'
          }`}
        >
          {status.status}
        </span>
      </div>

      {status.progress && (
        <div className="mt-2 text-sm text-gray-600">
          <pre className="bg-gray-50 p-2 rounded text-xs overflow-auto">
            {JSON.stringify(status.progress, null, 2)}
          </pre>
        </div>
      )}

      {status.error && (
        <div className="mt-2 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
          {status.error}
        </div>
      )}

      {isPolling && (
        <div className="mt-3 flex items-center space-x-2 text-sm text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
          <span>Polling for updates...</span>
        </div>
      )}
    </div>
  )
}

