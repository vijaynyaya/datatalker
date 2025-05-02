from datatalker.ogdp import OGDProxy
from pymongo import MongoClient
import traceback
import os


def main(mongodb_url: str, ogd_api_key: str):
    # get db connection
    client = MongoClient(mongodb_url)
    collection_name = "datatalker"
    db = client[collection_name]

    # initalize ODGP
    ogd = OGDProxy(api_key=ogd_api_key)

    # fetch catalogs
    responses = ogd.get_all(ogd.catalogs)
    catalogs = [
        catalog
        for response in responses
        for catalog in response["data"]["rows"]
    ]

    # store catalogs in a mongodb collection
    catalogs_collection_name = "ogd_catalogs"
    ogd_catalogs = db[catalogs_collection_name]
    ogd_catalogs.insert_many(catalogs)

    # log catalog statistics
    catalog_count = ogd_catalogs.count_documents({})
    print(f"Pulled {catalog_count} catalogs from OGD Platform.")

    # fetch resources
    responses = ogd.get_all(ogd.resources)
    resources = [
        resource
        for response in responses
        for resource in response["records"]
    ]

    # store resources in a mongodb collection
    resources_collection_name = "ogd_resources"
    ogd_resources = db[resources_collection_name]
    
    # NOTE: couldn't insert four resources due to BJSON object size too large error
    failures = list()
    for doc in resources:
        try:
            ogd_resources.insert_one(doc)
        except:
            failures.append(doc)
            traceback.print_exc()
    
    # log resource statistics
    resource_count = ogd_resources.count_documents({})
    fail_count = len(failures)
    print(f"Pulled {resource_count} resources from OGD Platform.")
    if fail_count:
        print(f"Failed to pull {fail_count} resources.")


if __name__ == "__main__":    
    # get parameters from environment vairables
    MONGODB_URL = os.environ["MONGODB_URL"]
    OGDP_API_KEY = os.environ["OGDP_API_KEY"]

    main(MONGODB_URL, OGDP_API_KEY)
