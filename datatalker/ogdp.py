import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from typing import Any
from multiprocessing import Pool, cpu_count
from typing import Literal

class OGDProxy:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.backend_url = "https://www.data.gov.in/backend"
        self.api_url = "https://api.data.gov.in"
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=5, max=60),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _make_request(self, url: str, method = "GET", **kwargs) -> requests.Response:
        response = requests.request(method=method.upper(), url=url, **kwargs)
        response.raise_for_status()
        return response
    
    def get_all(self, endpoint_method, batch_size=1000, params = dict()):
        """Fetch all the records from a paginated endpoint"""
        # get the total number of records
        initial_resp = endpoint_method(0, 1, params)
        total_records = initial_resp["total"]

        args = [
            (i, batch_size, params)
            for i in range(0, total_records, batch_size)
        ]

        with Pool(cpu_count()) as pool:
            responses = pool.starmap(endpoint_method, args)
        
        return responses
    
    def catalogs(self, offset: int = 0, limit: int = 10, params=dict()):
        """Fetch the list of catalogs"""
        url = self.backend_url + "/dmspublic/v1/catalogs"
        params["offset"] = offset
        params["limit"] = limit
        return self._make_request(url, params=params).json()
    
    def catalog_metadata(self, catalog_uuid: str, params=dict()) -> dict:
        """Fetch catalog information from backend"""
        url = self.backend_url + f"/dataapi/v1/catalog/{catalog_uuid}"
        params["format"] = "json"
        return self._make_request(url, params=params).json()
    
    def get_all_catalog_metadata(self, uuids: list[str]):
        """Fetch metadata for all the catalogs using catalog uuid"""
        # TODO: rate limit is very prohibitive, fails after a few concurrent requests
        with Pool(cpu_count()) as pool:
            args = [
                (uuid, dict())
                for uuid in uuids
            ]
            responses = pool.starmap(self.catalog_metadata, args)
        
        return responses    
    
    def catalog(self, catalog_uuid: str,  offset: int = 0, limit: int = 10, format: Literal["json", "csv"]="json", params=dict()):
        """Fetch catalog records using OGD API"""
        url = self.api_url + f"/catalog/{catalog_uuid}"
        params["api-key"] = self.api_key
        params["format"] = format
        params["offset"] = offset
        params["limit"] = limit
        return self._make_request(url, params=params)
    
    def resources(self, offset = 0, limit = 10, params = dict()):
        """Fetch resources"""
        url = self.api_url + "/lists"
        params["format"] = "json"
        params["offset"] = offset
        params["limit"] = limit
        return self._make_request(url, params=params).json()

    
    def resources_by_catalog_nid(self, catalog_nid: int, offset = 0, limit = 10, params=dict()):
        """Fetch resources belonging to a catalog using catalog nid"""
        url = self.backend_url + "/dmspublic/v1/resources"
        params["filters[catalog_reference]"] = catalog_nid
        params["offset"] = offset
        params["limit"] = limit
        return self._make_request(url, params=params)
    
    def get_all_resources_by_catalog_nid(self, catalog_nid: int, batch_size=100,  params=dict()):
        """Fetch all resources belonging to a catalog using catalog nid"""
        # get the total number of resources
        initial_resp = self.resources_by_catalog(catalog_nid, limit=1)
        total_records = initial_resp["total"]

        args = [
            (catalog_nid, i, batch_size, params)
            for i in range(0, total_records, batch_size)
        ]

        with Pool(cpu_count()) as pool:
            responses = pool.starmap(self.resources_by_catalog, args)
        
        return responses
    
    def prep_filtering_params(self, filters=dict()):
        pass


class DocumentAdapter:

    @staticmethod
    def embed_catalog_content(catalog: dict[str, Any]):
        ctlg_keys = catalog.keys()
        parts = [
            f"Title: {catalog.get('title', ['Unknown'])[0]}",
            f"Description: {catalog.get('body:value', [''])[0]}",
            f"Keywords: {catalog.get('keywords')}",
            f"Frequency: {catalog.get('frequency', ['Unknown'])[0]}",
            f"Open Government Data Site: {catalog.get('ogpl_module_domain_name')}"
            f"Government Type: {catalog.get('govt_type')}",
        ]
        for key in ctlg_keys:
            if key.startswith("field"):
                fmt_key = key.replace(r"_", " ").replace(":", " ").removeprefix("field ").title()
                line = f"{fmt_key}: {catalog[key]}"
                parts.append(line)
        return "\n".join(parts)

    @staticmethod
    def from_catalog(catalog: dict[str, Any]):
        return dict(
            type="dataset",
            url=f"https://data.gov.in{catalog.get('node_alias')[0]}",
            interface="ogd:catalog",
            title=catalog.get("title", ["Unkown Title"])[0],
            content=DocumentAdapter.embed_catalog_content(catalog),
            uuid=catalog["uuid"][0],
            nid=catalog["nid"][0],
            vid=catalog["vid"][0],
            is_api_available=catalog["is_api_available"][0] in {"1", 1}
        )