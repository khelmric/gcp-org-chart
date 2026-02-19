# asset_tools.py

from google.cloud import asset_v1
from googleapiclient import discovery
from google.protobuf.json_format import MessageToDict
from google.cloud.asset_v1.types import ResourceSearchResult
from googleapiclient.errors import HttpError

def get_resources(resource_id: str):
    exception_error_msg = ""
    project_ids = []
    asset_client = asset_v1.AssetServiceClient()
    # Asset types: https://cloud.google.com/asset-inventory/docs/asset-types
    filter_asset_types = [
        "cloudresourcemanager.googleapis.com/Project",
        "cloudresourcemanager.googleapis.com/Folder",
        "cloudresourcemanager.googleapis.com/Organization",
    ]

    resource_types = ["organization", "folder", "project"]
    detected_type = "invalid"
    resources_raw = None

    for rtype in resource_types:
        scope = f"{rtype}s/{resource_id}"
        try:
            resources_raw = asset_client.search_all_resources(
                asset_types=filter_asset_types,
                scope=scope,
            )
            detected_type = rtype
            break
        except Exception as e:
            exception_error_msg = e
            print(e)
            continue

    resources_list = []
    detected_display_name = ""
    parent_resource_id = "" 
    has_org = False
    last_folder_or_project = None

    if resources_raw:
        for res in resources_raw:
            proto_obj = res._pb
            r = MessageToDict(proto_obj, preserving_proto_field_name=True)

            resources_list.append(r)

            # Track if Organization exists
            if r.get("asset_type") == "cloudresourcemanager.googleapis.com/Organization":
                has_org = True

            # Track last folder/project
            if r.get("asset_type") in (
                "cloudresourcemanager.googleapis.com/Folder",
                "cloudresourcemanager.googleapis.com/Project",
            ):
                last_folder_or_project = r
                
            ## TESTING SA_KEYS
                
            if r.get("asset_type") in (
                "cloudresourcemanager.googleapis.com/Project",
            ):
                project_ids.append(r.get("name", "").split("/")[-1])
                
            ## /TESTING SA_KEYS

            # Check display_name match right away
            if r.get("name", "").split("/")[-1] == resource_id:
                detected_display_name = r.get("display_name", "")
                parent_resource_id = r.get("parent_full_resource_name", "").split("/")[-1]
                
    # get_user_managed_keys_for_projects(project_ids)

    # After loop: add synthetic organization if missing
    if not has_org and last_folder_or_project and "organization" in last_folder_or_project:
        org_field = last_folder_or_project["organization"]  # e.g. "organizations/599510563883"
        org_id = org_field.split("/")[-1]

        org_entry = {
            "name": f"//cloudresourcemanager.googleapis.com/{org_field}",
            "asset_type": "cloudresourcemanager.googleapis.com/Organization",
            "display_name": org_id,
        }
        resources_list.append(org_entry)
        
        if parent_resource_id and parent_resource_id != org_id:
            parent_entry = {
                "name": f"//cloudresourcemanager.googleapis.com/{parent_resource_id}",
                "asset_type": "cloudresourcemanager.googleapis.com/Folder",
                "display_name": "Unknown",
                "parent_full_resource_name": f"//cloudresourcemanager.googleapis.com/{org_field}",
            }
            resources_list.append(parent_entry)
            
    # Print a specific type for debug
    # for resource in resources_list:
    #     if resource.get('asset_type') == 'iam.googleapis.com/ServiceAccount':
    #         print(resource)
    
    return detected_type, detected_display_name, resources_list, exception_error_msg

from googleapiclient import discovery
from googleapiclient.errors import HttpError

def get_user_managed_keys_for_projects(project_ids):
    iam_service = discovery.build("iam", "v1", cache_discovery=False)
    results = {}

    for project_id in project_ids:
        user_keys = []

        try:
            request = iam_service.projects().serviceAccounts().list(name=f"projects/{project_id}")
            while request is not None:
                response = request.execute()
                for sa in response.get("accounts", []):
                    sa_name = sa["name"]

                    try:
                        key_request = iam_service.projects().serviceAccounts().keys().list(name=sa_name)
                        while key_request is not None:
                            key_response = key_request.execute()
                            for key in key_response.get("keys", []):
                                if key.get("keyType") == "USER_MANAGED":
                                    user_keys.append({
                                        "project_id": project_id,
                                        "service_account": sa_name,
                                        "key_id": key.get("name", "").split("/")[-1],
                                        "valid_after": key.get("validAfterTime"),
                                        "valid_before": key.get("validBeforeTime"),
                                        "algorithm": key.get("keyAlgorithm"),
                                    })

                            # ✅ FIXED: use discovery.list_next, not on the object
                            key_request = discovery.list_next(
                                previous_request=key_request,
                                previous_response=key_response
                            )

                    except HttpError as e:
                        if e.resp.status in (403, 404):
                            print(f"[WARN] Could not list keys for {sa_name} in {project_id}: {e}")
                        else:
                            raise

                # ✅ FIXED here as well
                request = discovery.list_next(
                    previous_request=request,
                    previous_response=response
                )

        except HttpError as e:
            if e.resp.status == 404:
                print(f"[WARN] IAM API not enabled or project not found: {project_id}")
                continue
            elif e.resp.status == 403:
                print(f"[WARN] Access denied for project {project_id}")
                continue
            else:
                raise

        results[project_id] = user_keys

    print(results)
    return results