"""API client for communicating with the AETHERA backend."""
import os
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime


API_BASE_URL = os.getenv("API_URL", "http://localhost:8001")
TIMEOUT = 10  # seconds


class APIError(Exception):
    """Custom exception for API errors."""
    pass


def _make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
) -> Any:
    """Make an HTTP request to the API."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=TIMEOUT)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, timeout=TIMEOUT)
            else:
                response = requests.post(url, json=data, timeout=TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, timeout=TIMEOUT)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        # DELETE requests may return 204 No Content, which has no response body
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()
    
    except requests.exceptions.Timeout:
        raise APIError("Request timeout - the server took too long to respond")
    except requests.exceptions.ConnectionError:
        raise APIError("No response from server - is the API running?")
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        if e.response:
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail") or error_data.get("message", "")
            except ValueError:
                error_detail = e.response.text
        raise APIError(error_detail or str(e))
    except Exception as e:
        raise APIError(f"Unexpected error: {str(e)}")


# Type definitions (using TypedDict would require typing_extensions)
class Project:
    """Project data structure."""
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.country: Optional[str] = data.get("country")
        self.sector: Optional[str] = data.get("sector")
        self.created_at: str = data["created_at"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "sector": self.sector,
            "created_at": self.created_at,
        }


class ProjectsAPI:
    """API client for projects endpoints."""
    
    @staticmethod
    def list() -> List[Project]:
        """List all projects."""
        data = _make_request("GET", "/projects")
        return [Project(item) for item in data]
    
    @staticmethod
    def get(project_id: str) -> Project:
        """Get a project by ID."""
        data = _make_request("GET", f"/projects/{project_id}")
        return Project(data)
    
    @staticmethod
    def create(name: str, country: Optional[str] = None, sector: Optional[str] = None) -> Project:
        """Create a new project."""
        data = {"name": name}
        if country:
            data["country"] = country
        if sector:
            data["sector"] = sector
        
        response = _make_request("POST", "/projects", data=data)
        return Project(response)
    
    @staticmethod
    def delete(project_id: str) -> None:
        """Delete a project."""
        _make_request("DELETE", f"/projects/{project_id}")


class RunsAPI:
    """API client for runs endpoints."""
    
    @staticmethod
    def list() -> List[Dict[str, Any]]:
        """List all runs."""
        return _make_request("GET", "/runs")
    
    @staticmethod
    def get(run_id: str) -> Dict[str, Any]:
        """Get a run by ID."""
        return _make_request("GET", f"/runs/{run_id}")
    
    @staticmethod
    def create(project_id: str, aoi_geojson: Optional[Dict[str, Any]] = None,
               aoi_path: Optional[str] = None, project_type: str = "solar",
               country: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new analysis run."""
        data: Dict[str, Any] = {"project_type": project_type}
        if aoi_geojson:
            data["aoi_geojson"] = aoi_geojson
        if aoi_path:
            data["aoi_path"] = aoi_path
        if country:
            data["country"] = country
        if config:
            data["config"] = config
        
        return _make_request("POST", f"/projects/{project_id}/runs", data=data)
    
    @staticmethod
    def get_results(run_id: str) -> Dict[str, Any]:
        """Get comprehensive results for a run."""
        return _make_request("GET", f"/runs/{run_id}/results")
    
    @staticmethod
    def get_legal(run_id: str) -> Dict[str, Any]:
        """Get legal compliance results for a run."""
        return _make_request("GET", f"/runs/{run_id}/legal")
    
    @staticmethod
    def export(run_id: str) -> bytes:
        """Export run package as ZIP."""
        url = f"{API_BASE_URL}/runs/{run_id}/export"
        response = requests.get(url, timeout=60)  # Longer timeout for file downloads
        response.raise_for_status()
        return response.content
    
    @staticmethod
    def get_biodiversity_layer(run_id: str, layer: str) -> Dict[str, Any]:
        """Get biodiversity layer GeoJSON."""
        return _make_request("GET", f"/runs/{run_id}/biodiversity/{layer}")


class TasksAPI:
    """API client for tasks endpoints."""
    
    @staticmethod
    def get_status(task_id: str) -> Dict[str, Any]:
        """Get task status."""
        return _make_request("GET", f"/tasks/{task_id}")
    
    @staticmethod
    def cancel(task_id: str) -> Dict[str, Any]:
        """Cancel a task."""
        return _make_request("DELETE", f"/tasks/{task_id}")


class LayersAPI:
    """API client for base layer endpoints."""
    
    @staticmethod
    def get_corine_tile_url(z: int, x: int, y: int, country: Optional[str] = None) -> str:
        """Get URL for a CORINE vector tile.
        
        Args:
            z: Zoom level (0-14)
            x: Tile X coordinate
            y: Tile Y coordinate
            country: Optional country code (e.g., 'ITA', 'GRC')
        
        Returns:
            URL to the vector tile endpoint
        """
        url = f"{API_BASE_URL}/tiles/corine/{z}/{x}/{y}.mvt"
        if country:
            url += f"?country={country}"
        return url
    
    @staticmethod
    def get_corine_tiles_metadata(country: Optional[str] = None) -> Dict[str, Any]:
        """Get metadata about CORINE vector tiles."""
        url = f"{API_BASE_URL}/tiles/corine/metadata"
        params = {"country": country} if country else {}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except ValueError:
                error_detail = e.response.text if e.response else str(e)
            raise APIError(error_detail)
    
    @staticmethod
    def get_natura2000(country: Optional[str] = None) -> Dict[str, Any]:
        """Get Natura 2000 layer, optionally filtered by country."""
        url = f"{API_BASE_URL}/layers/natura2000"
        params = {}
        if country:
            params["country"] = country
        try:
            # Country-filtered datasets should load faster
            timeout = 60 if country else 120
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise APIError("Request timed out. Try selecting a specific country to reduce dataset size.")
        except requests.exceptions.HTTPError as e:
            # Re-raise as APIError with detail message
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except ValueError:
                error_detail = e.response.text if e.response else str(e)
            raise APIError(error_detail)
    
    @staticmethod
    def get_corine(country: Optional[str] = None) -> Dict[str, Any]:
        """Get CORINE Land Cover layer, optionally filtered by country."""
        url = f"{API_BASE_URL}/layers/corine"
        params = {}
        if country:
            params["country"] = country
        try:
            # CORINE files are large even when country-specific (237 MB for Italy)
            # Give more time for GeoJSON conversion
            timeout = 180 if country else 300  # 3 minutes for country, 5 minutes for full
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise APIError("Request timed out. The CORINE dataset is very large and may take several minutes to load. Please wait and try again, or disable this layer for now.")
        except requests.exceptions.HTTPError as e:
            # Re-raise as APIError with detail message
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except ValueError:
                error_detail = e.response.text if e.response else str(e)
            raise APIError(error_detail)


class ReportsAPI:
    """API client for reports endpoints."""
    
    @staticmethod
    def generate(run_id: str, template_name: str = "enhanced_report.md.jinja", 
                 format: str = "markdown", enable_rag: bool = True) -> Dict[str, Any]:
        """Generate a report for a run."""
        data = {
            "run_id": run_id,
            "template_name": template_name,
            "format": format,
            "enable_rag": enable_rag,
        }
        return _make_request("POST", "/reports/generate", data=data)
    
    @staticmethod
    def list(project_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all reports."""
        params = {}
        if project_id:
            params["project_id"] = project_id
        if status:
            params["status"] = status
        response = _make_request("GET", "/reports", params=params)
        return response.get("reports", [])
    
    @staticmethod
    def get(report_id: str) -> Dict[str, Any]:
        """Get a report by ID."""
        return _make_request("GET", f"/reports/{report_id}")
    
    @staticmethod
    def export(report_id: str, format: str = "pdf") -> bytes:
        """Export a report in various formats."""
        url = f"{API_BASE_URL}/reports/{report_id}/export?format={format}"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.content


# Convenience instances
projects_api = ProjectsAPI()
runs_api = RunsAPI()
tasks_api = TasksAPI()
layers_api = LayersAPI()
reports_api = ReportsAPI()

