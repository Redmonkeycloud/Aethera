import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
})

// Add response interceptor for better error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      error.message = 'Request timeout - the server took too long to respond'
    } else if (error.response) {
      // Server responded with error status
      error.message = error.response.data?.detail || error.response.data?.message || error.message
    } else if (error.request) {
      // Request made but no response
      error.message = 'No response from server - is the API running?'
    }
    return Promise.reject(error)
  }
)

// Types
export interface Project {
  id: string
  name: string
  country?: string
  sector?: string
  created_at: string
}

export interface ProjectCreate {
  name: string
  country?: string
  sector?: string
}

export interface RunSummary {
  run_id: string
  project_id?: string
  project_type: string
  created_at: string
  status: string
}

export interface RunDetail extends RunSummary {
  outputs: Record<string, Record<string, string>>
}

export interface RunCreate {
  aoi_geojson?: GeoJSON.Feature | GeoJSON.FeatureCollection
  aoi_path?: string
  project_type: string
  country?: string
  config?: Record<string, unknown>
}

export interface RunCreateResponse {
  task_id: string
  run_id?: string
  status: string
  message: string
}

export interface TaskStatus {
  task_id: string
  status: string
  project_id?: string
  run_id?: string
  progress?: Record<string, unknown>
  error?: string
}

// API functions
export const projectsApi = {
  list: () => apiClient.get<Project[]>('/projects').then((res) => res.data),
  get: (id: string) => apiClient.get<Project>(`/projects/${id}`).then((res) => res.data),
  create: (data: ProjectCreate) =>
    apiClient.post<Project>('/projects', data).then((res) => res.data),
}

export const runsApi = {
  list: () => apiClient.get<RunSummary[]>('/runs').then((res) => res.data),
  get: (id: string) => apiClient.get<RunDetail>(`/runs/${id}`).then((res) => res.data),
  create: (projectId: string, data: RunCreate) =>
    apiClient.post<RunCreateResponse>(`/projects/${projectId}/runs`, data).then((res) => res.data),
  getResults: (id: string) =>
    apiClient.get(`/runs/${id}/results`).then((res) => res.data),
  getLegal: (id: string) =>
    apiClient.get(`/runs/${id}/legal`).then((res) => res.data),
  export: (id: string) =>
    apiClient.get(`/runs/${id}/export`, { responseType: 'blob' }).then((res) => res.data),
  getBiodiversityLayer: (id: string, layer: string) =>
    apiClient.get<GeoJSON.FeatureCollection>(`/runs/${id}/biodiversity/${layer}`).then((res) => res.data),
}

export const tasksApi = {
  getStatus: (taskId: string) =>
    apiClient.get<TaskStatus>(`/tasks/${taskId}`).then((res) => res.data),
  cancel: (taskId: string) =>
    apiClient.delete(`/tasks/${taskId}`).then((res) => res.data),
}

