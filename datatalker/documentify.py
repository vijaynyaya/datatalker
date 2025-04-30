from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class Document:
    """Dataclass to represent a document"""
    page_content: str
    metadata: Dict[str, Any]


def fmt_resource_document(resource: Dict[str, Any], package: Dict[str, Any]) -> Document:
    """Create a document from a resource"""
    content = f"""
Resource: {resource.get('name', '')}
Resource ID: {resource.get('id', '')}
SKU: {resource.get('sku', '')}
Format: {resource.get('format', '')}
Description: {resource.get('description', '')}
Data Insights: {resource.get('data_insights', '')}
Methodology: {resource.get('methodology', '')}
Frequency: {resource.get('frequency', '')}
Granularity: {resource.get('granularity', '')}
Years Covered: {resource.get('years_covered', '')}
Data Source: {resource.get('data_extraction_page', '')}

Part of Package: {package.get('title', '')}
"""
    metadata = {
        "source_type": "resource",
        "id": resource.get("id", ""),
        "name": resource.get("name", ""),
        "package_name": package.get("name", ""), # slug
        "package_title": package.get("title", ""),
        "sku": resource.get("sku", ''),
        "url": resource.get("url", "")
    }
    return Document(page_content=content, metadata=metadata)

def fmt_field_list(fields: Dict[str, Any]) -> str:
    """Format a list of fields on a datastore"""
    fmt_field_list = [
        f"""
Column Name: {field.get("id", "")}
Data Type: {field.get("type", "")}
Vaiable Description: {field.get("info", {}).get("label", "")}
Measurement Unit: {field.get("info", {}).get("units", "")}
"""
        for field in fields
    ]
    return "".join(fmt_field_list)

def fmt_datastore_document(datastore_info: Dict[str, Any]) -> Document:
    """Create a document from a datastore"""
    datastore_meta = datastore_info.get("meta", {})
    size_bytes = datastore_meta.get("", 0)
    size_mb = size_bytes / (1024 * 1024) if size_bytes else 0
    content = f"""
Datastore Information:
Record Count: {datastore_meta.get('count', 'Unknown')}
Size: {size_mb:.2f} MB
Variables:
{fmt_field_list(datastore_info.get("fields", []))}
"""
    metadata = {
        "source_type": "datastore",
        "id": datastore_meta.get("id", ""),
        "record_count": datastore_meta.get("count", 0),
    }
    return Document(page_content=content, metadata=metadata)

def fmt_package_document(package: Dict[str, Any]) -> Document:
    """Create a document from a package"""
    content = f"""
Name: {package.get('name', '')}
Package ID: {package.get('title', '')}
Description: {package.get('notes', '')}
Source Name: {package.get('source_name', '')}
Sectors: {"; ".join(package.get('sectors', []))}

Resources:
{"\n".join(
        f"{i+1}. {resource.get('name', '')} (ID: {resource.get('id', '')})"
        for i, resource in enumerate(package.get("resources", []))
    )}
"""
    metadata = {
        "source_type": "package",
        "id": package.get("id", ""),
        "name": package.get("name", ""),
        "title": package.get("title", ""),
    }
    return Document(page_content=content, metadata=metadata)