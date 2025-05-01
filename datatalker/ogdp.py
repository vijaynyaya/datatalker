import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
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
        params["api_key"] = self.api_key
        params["format"] = format
        params["offset"] = offset
        params["limit"] = limit
        return self._make_request(url, params=params)
    
    def prep_filtering_params(self, filters=dict()):
        pass