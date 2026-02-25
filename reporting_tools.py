# reporting_tools.py

import json
from common import *

def asset_data2html(resources_list, resource_id, resource_display_name, resource_type):
    chart_rows = []
    resman_array = []
    projects_by_parent = {}
    
    resman_type_counts = {
        "organization": 0,
        "folder": 0,
        "project": 0
    }

    def short_name(full_name: str) -> str:
        return full_name.split("/")[-1] if full_name else ""

    def add_project(parent_id: str, project_id: str, project_name: str, project_create_time: str) -> None:
        if not parent_id:
            return
        projects_by_parent.setdefault(parent_id, []).append({
            "id": project_id,
            "name": project_name,
            "create_time": project_create_time,
        })

    for res in resources_list:
        # COMMON
        full_name = res.get("name", "")
        name = short_name(full_name)
        display_name = res.get("display_name", name)
        parent_full = res.get("parent_full_resource_name", "")
        parent = short_name(parent_full)
        create_time_raw = res.get("create_time", "")
        create_time = create_time_raw.replace("T", " ").replace("Z", "")[:-3]
        tooltip_text = f"Name: {display_name}\nID: {name}\nCreated: {create_time}"
        state = res.get("state", "")
        labels = res.get("labels", {})
        tag_values = res.get("tag_values", [])
        
        print(res)
        
        # RESMAN
        if res.get("asset_type") in (
                "cloudresourcemanager.googleapis.com/Project",
                "cloudresourcemanager.googleapis.com/Folder",
                "cloudresourcemanager.googleapis.com/Organization",
            ):
            res_type = res.get("asset_type", "").split("/")[-1].lower()
            
            if res.get("state", "") in ("ACTIVE", ""):
                resman_type_counts[res_type] += 1
                # if res_type in ("project", "folder"):
                #     resource_type_icon = f"{resource_type_icons[res_type]}<br>"
                # else:
                #     resource_type_icon = f"{resource_type_icons[res_type]}"

                if res_type == "project":
                    add_project(parent, name, display_name, create_time)
                else:
                    icon_html = resource_type_icons.get(res_type, "")
                    type_label = ""
                    if res_type == "organization":
                        type_label = "<div class=\"org-chart-type\"><strong>Organization</strong></div>"
                    node_html = (
                        f"<div class=\"org-chart-node\" data-node-id=\"{name}\" data-node-type=\"{res_type}\" data-tooltip=\"{tooltip_text}\">"
                        f"<div class=\"org-chart-icon\">{icon_html}</div>"
                        f"{type_label}"
                        f"<div class=\"org-chart-text\">{display_name}</div>"
                        "</div>"
                    )

                    chart_rows.append([
                        {
                            "v": name,
                            "f": node_html,
                        },
                        parent,
                        tooltip_text,
                    ])

                resman_array.append({
                    "type": res_type.capitalize(),
                    "name": display_name,
                    "id": name,
                    "create_time": create_time,
                    "state": state,
                    "labels": labels,
                    "tag_values": tag_values,
                })

        # Ignore other asset types for report output
        else:
            continue

    project_icon = resource_type_icons.get("project", "")
    max_cluster_size = 10
    for parent_id, projects in projects_by_parent.items():
        if not projects:
            continue
        ordered_projects = sorted(projects, key=lambda p: p.get("name", ""))

        for start_idx in range(0, len(ordered_projects), max_cluster_size):
            cluster = ordered_projects[start_idx:start_idx + max_cluster_size]
            previous_id = parent_id
            for project in cluster:
                project_id = project.get("id", "")
                project_name = project.get("name", "")
                project_create_time = project.get("create_time", "")
                if not project_id:
                    continue
                project_tooltip = f"Name: {project_name}\nID: {project_id}\nCreated: {project_create_time}"
                node_html = (
                    f"<div class=\"org-chart-node org-chart-node-row\" data-node-id=\"{project_id}\" data-node-type=\"project\" data-tooltip=\"{project_tooltip}\">"
                    f"<div class=\"org-chart-icon\">{project_icon}</div>"
                    f"<div class=\"org-chart-text\">{project_name}</div>"
                    "</div>"
                )
                chart_rows.append([
                    {
                        "v": project_id,
                        "f": node_html,
                    },
                    previous_id,
                    project_tooltip,
                ])
                previous_id = project_id
    
    # Only render org chart HTML
    resource_hierarchy_html = f'''<div id="chart-wrapper">
        <div class="chart-controls">
            <label id="resource-hierarchy-chart-zoom-label" for="resource-hierarchy-chart-zoom" style="vertical-align: top;visibility: hidden;">Chart zoom </label>
            <input type="range" class="range" id="resource-hierarchy-chart-zoom" min="1" max="20" value="10" step="0.2"
                title="zoom" style="vertical-align: top;visibility: hidden;"/>
        </div>
        <div id="resource-hierarchy-chart-scale">
            <div id="resource-hierarchy-chart"></div>
        </div>
    </div>'''
           
    chart_data = json.dumps(chart_rows)
    return chart_data, resource_hierarchy_html