from reporting_tools import asset_data2html
from auth_tools import get_authenticated_account
from asset_tools import get_resources
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

account, project = get_authenticated_account()

### ROUTES ###########################################

@app.route("/", methods=["GET", "POST"])
def index():
    resource_id = ""
    resources = []
    resource_type = ""
    resource_display_name = ""
    resource_hierarchy_chart_data = ""
    resource_hierarchy_html = ""
    error_msg = ""
    exception_error_msg = ""

    resource_id = request.args.get("resourceId", "")
    
    if account == "unauthenticated user":
        error_msg = error_msg + f"""<br>ERROR - No authenticated user found, please login with your user:<pre><code>
        gcloud auth application-default login
        gcloud auth application-default set-quota-project [PROJECT_ID]
        </code></pre>"""
        
    # Get inputs
    if request.method == "GET" and account != "unauthenticated user":
        try:
            if resource_id:
                resource_type, resource_display_name, resources, exception_error_msg = get_resources(resource_id)
                if resources:
                    resource_hierarchy_chart_data, resource_hierarchy_html = asset_data2html(resources, resource_id, resource_display_name, resource_type)
        except Exception as e:
            print(e)
            
    if resource_type == "invalid":
        error_msg = f"{error_msg} <br>ERROR - Wrong resource ID, quota issue or missing permissions.<br> ({exception_error_msg})" 
        
    # Render template
    return render_template("index.html",
                           resource_id=resource_id,
                           current_account=account,
                           error_msg=error_msg,
                           resource_hierarchy_chart_data = resource_hierarchy_chart_data,
                           resource_hierarchy_html = resource_hierarchy_html
                           )


### MAIN ###########################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)