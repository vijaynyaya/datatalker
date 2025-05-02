from datatalker.ckan import CKANProxy
from pymongo import MongoClient
import traceback
import os


def main(mongodb_url: str, ckan_url: str):
    # get db connection
    client = MongoClient(mongodb_url)
    collection_name = "datatalker"
    db = client[collection_name]

    # initialize CKAN
    ckan = CKANProxy(ckan_url)

    # fetch packages
    pkg_list = ckan.get_package_list()
    packages = [
        ckan.get_package(pkg_slug)
        for pkg_slug in pkg_list
    ]

    # store packages in a mongodb collection
    packages_collection_name = "ckan_packages"
    ckan_pkgs = db[packages_collection_name]
    ckan_pkgs.insert_many(packages)

    # store resources in a separate mongodb collection
    resources_collection_name = "ckan_resources"
    ckan_rsrcs = db[resources_collection_name]
    rsrcs = [
        rsrc
        for pkg in packages
        for rsrc in pkg["resources"]
    ]
    ckan_rsrcs.insert_many(rsrcs)

    # log package statistics
    pkg_count = ckan_pkgs.count_documents({})
    rsrc_count = ckan_rsrcs.count_documents({})
    print(f"Pulled {pkg_count} packages containing {rsrc_count} resrouces from CKAN.")

    # fetch datastores
    rsrc_ids = ckan_rsrcs.distinct("id")
    datastores = list()
    failures = list()
    print("Pulling datastores...")
    print("You may ignore HTTP 404 errors, as they indicate the absence of certain datastores.")
    for rsrc_id in rsrc_ids:
        try:
            datastore = ckan.get_datastore_info(rsrc_id)
            datastores.append(datastore)
        except:
            traceback.print_exc()
            failures.append(rsrc_id)
    
    # store datastores in a mongodb collection
    datastores_collection_name = "ckan_datastores"
    ckan_dsts = db[datastores_collection_name]
    ckan_dsts.insert_many(datastores)

    # log datastore statistics
    ds_count = ckan_dsts.count_documents({})
    print(f"Pulled {ds_count} datastores from CKAN.")
    fail_count = len(failures)
    if fail_count:
        print(f"{fail_count} resources don't seem to have a datastore associated with them.")


if __name__ == "__main__":
    # get parameters from environment variables
    MONGODB_URL = os.environ['MONGODB_URL']
    CKAN_URL = os.environ['CKAN_URL']

    main(MONGODB_URL, CKAN_URL)