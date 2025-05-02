import requests
from typing import Dict, List, Any


class CKANProxy:
    """Class to load data from a CKAN instance"""
    
    def __init__(self, ckan_url: str, headers: Dict[str, str] = None):
        self.ckan_url = ckan_url.rstrip('/')
        self.headers = headers or {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        }
        
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the CKAN API"""
        url = f"{self.ckan_url}/api/3/action/{endpoint}"
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_package_list(self) -> List[str]:
        """Get list of all package IDs"""
        result = self._make_request("package_list")
        return result["result"]
    
    def get_package(self, package_id: str) -> Dict[str, Any]:
        """Get package details by ID"""
        result = self._make_request("package_show", {"id": package_id})
        return result["result"]
    
    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """Get resource details by ID"""
        result = self._make_request("resource_show", {"id": resource_id})
        return result["result"]
    
    def get_datastore_info(self, resource_id: str) -> Dict[str, Any]:
        result = self._make_request("datastore_info", {"id": resource_id})
        return result["result"]
    
    def datastore_search_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query on datastore"""
        result = self._make_request("datastore_search_sql", {"sql": sql})
        return result["result"]