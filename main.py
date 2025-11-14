from flask import Flask, request, render_template_string
from google.cloud import asset_v1
from google.protobuf.json_format import MessageToDict
import google.auth
import google.auth.transport.requests
import requests

resource_type_icons = {
    "project": "📌",
    "folder": "📁",
    "organization": "🏢"
}

app = Flask(__name__)


def get_resources(resource_id: str):
    asset_client = asset_v1.AssetServiceClient()
    filter_asset_types = [
        "cloudresourcemanager.googleapis.com/Project",
        "cloudresourcemanager.googleapis.com/Folder",
        "cloudresourcemanager.googleapis.com/Organization",
    ]
    
    resource_types = ["organization", "folder", "project"]
    detected_type = "invalid"
    resources_raw = None

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

            # check if org exists
            if r.get("asset_type") == "cloudresourcemanager.googleapis.com/Organization":
                has_org = True

            # last folder/project
            if r.get("asset_type") in (
                "cloudresourcemanager.googleapis.com/Folder",
                "cloudresourcemanager.googleapis.com/Project",
            ):
                last_folder_or_project = r

            if r.get("name", "").split("/")[-1] == resource_id:
                detected_display_name = r.get("display_name", "")
                parent_resource_id = r.get("parent_full_resource_name", "").split("/")[-1]
                
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
            
   
    return detected_type, detected_display_name, resources_list, exception_error_msg


def build_orgchart_rows(resources):
    chart_data = ""
    
    def short_name(full_name: str) -> str:
        return full_name.split("/")[-1] if full_name else ""

    for res in resources:
        name_full = res.get("name", "")
        name = short_name(name_full)
        display_name = res.get("display_name", "")
        parent_full = res.get("parent_full_resource_name")
        parent = short_name(parent_full)
        res_type = res.get("asset_type", "").split("/")[-1].lower()

        chart_data += f"""
            data.addRow([
                {{ v: '{name}', f: `{resource_type_icons.get(res_type, "")}<br><b>{display_name}</b>` }},
                '{parent}',
                '{name}'
            ]);
        """
    return chart_data


HTML_PAGE = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>GCP Resource Org Chart</title>

    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {packages:["orgchart"]});
      google.charts.setOnLoadCallback(drawChart);

      function drawChart() {
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'Name');
        data.addColumn('string', 'Parent');
        data.addColumn('string', 'Tooltip');
        
        {{ chart_data|safe }}
        
        var chart = new google.visualization.OrgChart(
            document.getElementById('chart_div')
        );

        chart.draw(data, {allowHtml: true,allowCollapse: true,compactRows: true,size: 'medium'});
        
      }
    </script>

    <style>
      body { font-family: Arial; margin: 20px; }
      input { padding: 6px; width: 260px; }
      button { padding: 6px 12px; }
      #chart_div { margin-top: 30px; }
    </style>
</head>
<body>

<h2>GCP Resource Hierarchy Org Chart</h2>

<form method="POST">
    <input type="text" name="resource_id" placeholder="Org / Folder / Project ID">
    <button type="submit">Show</button>
</form>

{% if error %}
  <p style="color:red;">Error: {{ error }}</p>
{% endif %}

<div id="chart_div"></div>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    chart_data = ""
    error = ""

    if request.method == "POST":
        resource_id = request.form.get("resource_id", "").strip()
        resource_type, resource_display_name, resources, exception_error_msg = get_resources(resource_id)

        chart_data = build_orgchart_rows(resources)

    return render_template_string(
        HTML_PAGE,
        chart_data=chart_data,
        error=error
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)