# reporting_tools.py

import re
import json
from collections import Counter
from common import *

# Default value ranges
DEFAULTS = {
    "ok_from": 90, "ok_to": 100,
    "warn_from": 20, "warn_to": 89,
    "crit_from": 0, "crit_to": 19
}
ALERT_SIGN = "&#10071; "

def asset_data2html(resources_list, resource_id, resource_display_name, resource_type):
    chart_rows = []
    resman_array = []
    
    resman_type_counts = {
        "organization": 0,
        "folder": 0,
        "project": 0
    }

    def short_name(full_name: str) -> str:
        return full_name.split("/")[-1] if full_name else ""

    for res in resources_list:
        # COMMON
        full_name = res.get("name", "")
        name = short_name(full_name)
        display_name = res.get("display_name", name)
        parent_full = res.get("parent_full_resource_name", "")
        parent = short_name(parent_full)
        create_time_raw = res.get("create_time", "")
        create_time = create_time_raw.replace("T", " ").replace("Z", "")[:-3]
        state = res.get("state", "")
        labels = res.get("labels", {})
        tag_values = res.get("tag_values", [])
        
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

                chart_rows.append([
                    {
                        "v": name,
                        "f": f"{resource_type_icons[res_type]}<br><b><div class=\"org-chart-element-text\">{display_name}</div></b>",
                    },
                    parent,
                    name,
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

# HTML FUNCTIONS ###########################################################

def create_gauge_html(
    value,
    value_type="",
    max_value=100,
    redFrom=0,
    redTo=25,
    yellowFrom=25,
    yellowTo=75,
    greenFrom=75,
    greenTo=100
):

    html = f"""
    <html>
    <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
        google.charts.load('current', {{'packages':['corechart']}});
        google.charts.setOnLoadCallback(drawChart);

        function drawChart() {{
        var data = google.visualization.arrayToDataTable([
            ['Vars', 'Percentage'],
            ['', {value/2}],
            ['', {(100-value)/2}],
            ['', 50]
        ]);

        // Choose color dynamically
        let mainColor, statusClass;
        if ({value} >= {DEFAULTS["ok_from"]}) {{
            mainColor = '#34c759'; // green
            statusClass = 'status-green';
        }} else if ({value} >= {DEFAULTS["warn_from"]}) {{
            mainColor = '#ff9500'; // orange
            statusClass = 'status-orange';
        }} else {{
            mainColor = '#ff3b30'; // red
            statusClass = 'status-red';
        }}

        var options = {{
            width: 220, height: 220,
            enableInteractivity: false,
            pieStartAngle: 270,
            pieHole: 0.6,
            legend: 'none',
            pieSliceText: 'none',
            tooltip: {{ trigger: 'none' }},
            backgroundColor: 'transparent',
            slices: {{
            0: {{ color: mainColor }},
            1: {{ color: '#e6e6e6' }},
            2: {{ color: 'transparent' }}
            }}
        }};

        var chart = new google.visualization.PieChart(document.getElementById('gauge_chart'));
        chart.draw(data, options);

        document.getElementById('gauge_text').innerHTML =
            '<span class="' + statusClass + '">' + {value} + '%</span>';
        }}
    </script>

    </head>
        <div class="result_row">
            <span class="result_label">Health</span>
        </div>
        <div class="result_row">
            <div class="gauge-container">
                <div id="gauge_chart"></div>
                <div id="gauge_text"></div>
            </div>
        </div>
    </html>
    """
    return html

def put_html_content_into_div(html, div_class):
    div_start = f"<div class='{div_class}'>"
    html.insert(0, div_start)
    html.append("</div>")
    return html

def build_html_content(
    main_div_id=None, main_div_class=None,
    title_id=None, title_class=None, title_text=None,
    intro_id=None, intro_class=None, intro_text=None,
    results=None,  # list of dicts [{title_id, title_class, title_text, content_id, content_class, content}]
    findings_title_id=None, findings_title_class=None, findings_title_text=None,
    findings_id=None, findings_class=None, findings_content=None
):
    """
    Builds an HTML structure where:
    - main div wraps everything
    - one optional title (h2)
    - one optional introduction div
    - multiple results sections (each can have h3 + div)
    - one findings section (single h3 + div)
    Every element is optional.
    """

    def tag(tag_name, content=None, _id=None, _class=None):
        """Helper to build HTML tags safely."""
        if content is None:
            return ""
        attrs = ""
        if _id:
            attrs += f' id="{_id}"'
        if _class:
            attrs += f' class="{_class}"'

        # ✅ Only skip wrapping if the content already starts with a full div-like tag
        if isinstance(content, str):
            stripped = content.strip().lower()
            if stripped.startswith("<div") or stripped.startswith("<section") or stripped.startswith("<article"):
                return content

        return f"<{tag_name}{attrs}>{content}</{tag_name}>"

    html_parts = []

    # h2 Title
    if title_text:
        html_parts.append(tag("h2", title_text, title_id, title_class))

    # Introduction div
    if intro_text:
        html_parts.append(tag("div", intro_text, intro_id, intro_class))

    # Multiple Results Sections
    if results:
        for r in results:
            if r.get("title_text"):
                html_parts.append(
                    tag("h3", r["title_text"], r.get("title_id"), r.get("title_class"))
                )
            if r.get("content"):
                html_parts.append(
                    tag("div", r["content"], r.get("content_id"), r.get("content_class"))
                )

    # Single Findings Section
    if findings_title_text:
        html_parts.append(tag("h3", findings_title_text, findings_title_id, findings_title_class))
    if findings_content:
        html_parts.append(tag("div", findings_content, findings_id, findings_class))

    # Wrap in main div
    inner_html = "\n".join(html_parts)
    if main_div_id or main_div_class:
        inner_html = tag("div", inner_html, main_div_id, main_div_class)
        
    return inner_html
   
def analyze_naming_convention(resources):
    """
    Analyze naming conventions and detect the most common prefix pattern.

    Args:
        resources (list): List of resource name strings.

    Returns:
        tuple: (score, message)
    """
    if not resources:
        return 2, "No resources provided."

    # Normalize names (lowercase, replace spaces)
    normalized = [r.lower().replace(" ", "-") for r in resources if isinstance(r, str)]
    
    # Collect possible prefixes (everything up to the first '-', '_', or space)
    prefixes = []

    for name in normalized:
        m = re.match(r"^([a-z0-9]+[-_])", name)
        if m:
            prefixes.append(m.group(1))

    if not prefixes:
        return 0, "No consistent prefix naming convention found."

    # Count most common prefix
    counter = Counter(prefixes)
    most_common_prefix, count = counter.most_common(1)[0]
    total = len(normalized)
    percentage = int((count * 100) / total)

    if count == total:
        value = 100
        message = f"All resources share the common prefix '{most_common_prefix}' ({count}/{total})."
    elif count > 1:
        value = percentage
        message = f"Partial naming convention detected with the prefix '{most_common_prefix}' ({count}/{total})."
    else:
        value = 0
        message = f"No consistent prefix naming convention found ({count}/{total})."

    return value, message

# OVERALL STATUS ###########################################################

def build_overall_status(overall_max_score, overall_score, overall_findings_count):
    overall_percentage = int((overall_score / overall_max_score) * 100) if overall_max_score > 0 else 0
    html_gauge = create_gauge_html(overall_percentage, "%")
    html_table = create_overall_findings_summary_html(overall_findings_count)
    
    if overall_percentage <= DEFAULTS["crit_to"]:
        overall_status = "<span class='status-red'>CRITICAL</span>"
    elif overall_percentage >= DEFAULTS["ok_from"]:
        overall_status = "<span class='status-green'>OK</span>"
    else:
        overall_status = "<span class='status-orange'>WARNING</span>"

    # Combine into a single HTML layout (side by side, left-aligned, close together)
    html = f"""
    <html>
      <body>
        <div class="result-container">
          <div class="content-result-container">
            {html_gauge}
          </div>
          <div class="content-result-container">
            <div class="result_row">
                <span class="result_label">Status</span>
            </div>
            <div class="result_row">
                <span class="result_value">{overall_status}</span>
            </div>
          </div>
          <div class="content-result-container">
            {html_table}
          </div>
        </div>
      </body>
    </html>
    """
    return html

def create_overall_findings_summary_html(overall_findings_count):
    # Define status labels for readability
    statuses = [
        "<span class='status-green'>OK</span>",
        "<span class='status-orange'>WARNING</span>",
        "<span class='status-red'>CRITICAL</span>"
    ]

    # Initialize containers for components contributing to each status
    status_components = {status: [] for status in statuses}
    status_totals = {status: 0 for status in statuses}

    # Process each component and its findings
    for component, ok, warning, critical in overall_findings_count:
        counts = [ok, warning, critical]
        for i, count in enumerate(counts):
            if count > 0:
                status = statuses[i]
                status_components[status].append(f"{component} ({count})")
                status_totals[status] += count

    # Build HTML table
    html = """
    <div class="content-result-container">
        <div class="result_row">
            <span class="result_label">Components</span>
        </div>
        <table class="report-table" border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse; text-align: left;">
            <tr style="background-color: #f2f2f2;">
                <th>Component name</th>
                <th>Status</th>
                <th>Count</th>
            </tr>
    """

    # Add rows only if there are findings
    for status in statuses:
        total = status_totals[status]
        if total > 0:
            components_str = ", ".join(status_components[status])
            html += f"""
            <tr>
                <td>{components_str}</td>
                <td>{status}</td>
                <td>{total}</td>
            </tr>
            """

    html += "</table></div>"
    return html

# FINDINGS ###########################################################

def resource_findings_percentage(resources, field_name):
    total_resources = len(resources)
    matching_resources = sum(1 for p in resources if p.get(field_name))
    if total_resources > 0:
        findings_percentage = (matching_resources / total_resources) * 100
    else:
        findings_percentage = 0
    return findings_percentage
    

def generate_findings_table(findings_rows):
    """
    Generic findings table generator.
    
    Args:
        findings_rows: list[dict] - each row should include optional thresholds:
            {
                "category": str,
                "scope": str,
                "result": str or float or int,
                "result_unit": str (optional),
                "description": str (optional),
                "ok_from": float (optional),
                "ok_to": float (optional),
                "warn_from": float (optional),
                "warn_to": float (optional),
                "crit_from": float (optional),
                "crit_to": float (optional)
            }

    Returns:
        html_table (str): Generated HTML table
        count_ok (int): Number of OK entries
        count_warn (int): Number of WARNING entries
        count_crit (int): Number of CRITICAL entries
    """

    count_ok = count_warn = count_crit = 0
    max_score = 0
    score = 0

    html = []
    html.append("""
        <table class="report-table">
          <thead>
            <tr><th>Category</th><th>Scope</th><th>Description</th><th>Result</th><th>Status</th></tr>
          </thead>
          <tbody>
    """)

    for row in findings_rows:
        category = row.get("category", "")
        scope = row.get("scope", "")
        description = row.get("description", "")
        result = row.get("result", "")
        result_unit = row.get("result_unit", "")

        # Merge defaults with provided values
        thresholds = {k: row.get(k, v) for k, v in DEFAULTS.items()}
        
        try:
            result_val = float(result)
        except (ValueError, TypeError):
            # Non-numeric result → UNKNOWN
            status = "<span class='status-gray'>UNKNOWN</span>"
            html.append(f"<tr><td>{category}</td><td>{scope}</td><td>{description}</td><td>{result} {result_unit}</td><td>{status}</td></tr>")
            continue

        max_score += 4

        # Determine status
        if thresholds["ok_from"] <= result_val <= thresholds["ok_to"]:
            status = "<span class='status-green'>OK</span>"
            count_ok += 1
            score += 4
        elif thresholds["warn_from"] <= result_val <= thresholds["warn_to"]:
            status = "<span class='status-orange'>WARNING</span>"
            count_warn += 1
            score += 3
        elif thresholds["crit_from"] <= result_val <= thresholds["crit_to"]:
            status = "<span class='status-red'>CRITICAL</span>"
            count_crit += 1
            score += 0
        else:
            status = "<span class='status-gray'>UNKNOWN</span>"

        html.append(
            f"<tr>"
            f"<td>{category}</td>"
            f"<td>{scope}</td>"
            f"<td>{description}</td>"
            f"<td>{result} {result_unit}</td>"
            f"<td>{status}</td>"
            f"</tr>"
        )

    html.append("</tbody></table>")

    return "\n".join(html), count_ok, count_warn, count_crit, max_score, score


# RESOURCE HIERARCHY ###########################################################

def generate_resman_results(rows, counts):
    
    max_score = 0
    score = 0
    findings_html = []
    resource_hierarchy_findings_html = []
    
    """
    Create HTML table with:
      1. Summary (type and count)
      2. Detailed list (type, name, ID)
    """
    # Define custom type ordering
    order = {"Organization": 0, "Folder": 1, "Project": 2}

    # Sort rows first by type (custom order), then by name (A-Z)
    rows_sorted = sorted(rows, key=lambda r: (order.get(r["type"], 99), r["name"].lower()))

    html_resource_types = []

    # Summary table (3 rows)
    html_resource_types.append("""
        <table class="report-table" >
          <thead>
            <tr><th>Resource type</th><th>Count</th></tr>
          </thead>
          <tbody>
    """)

    # Only include known types in custom order
    for t in order.keys():
        count = counts.get(t.lower(), 0)
        html_resource_types.append(f"<tr><td>{resource_type_icons_small[t.lower()]} {t}</td><td>{count}</td></tr>")

    html_resource_types.append("</tbody></table>")

    # Detailed resources table
    
    html_resource_list = []
    
    html_resource_list.append("""
        <table class="report-table sortable">
          <thead>
            <tr><th>Resource type</th><th>Name</th><th>ID</th><th>Create time</th><th>State</th><th>Tags<span class="tag">tag_value</span>/ Labels<span class="label">key: value</span></th></tr>
          </thead>
          <tbody>
    """)
    
    for row in rows_sorted:
        if row['state'] == "ACTIVE":
            res_state = f"<span class='state-green'>{row['state']}</span>"
        elif row['state'] == "":
            res_state = f"<span class='state-gray'>UNKNOWN</span>"
        else:
            res_state = f"<span class='state-orange'>{row['state']}</span>"
            
        # Build labels HTML
        labels_html = ""
        if 'labels' in row and row['labels']:
            labels_html = html_display_labels(row['labels'])
        
        # Build tag values HTML
        tags_html = ""
        if 'tag_values' in row and row['tag_values']:
            tags_html = html_display_tags(row['tag_values'])
            
            
        html_resource_list.append(f"<tr><td style='white-space: nowrap;'>{resource_type_icons_small[row['type'].lower()]} {row['type']}</td>"
                    f"<td>{row['name']}</td>"
                    f"<td>{row['id']}</td>"
                    f"<td style='white-space: nowrap;'>{row['create_time']}</td>"
                    f"<td>{res_state}</td>"
                    f"<td>{tags_html} {labels_html}</td>"
                    f"</tr>")

    html_resource_list.append("</tbody></table>")
    
    # return "\n".join(html_resource_types), "\n".join(html_resource_list), findings_html, max_score, score, findings_count
    return "\n".join(html_resource_types), "\n".join(html_resource_list), rows_sorted

# GENERIC RESULTS ###########################################################

def generate_generic_results(rows, columns):
    """
    Generic HTML table generator for different GCP resource types.

    Args:
        rows: list[dict] - extracted resource data
        columns: list[tuple] - (field_name, display_label)
    
    Returns:
        str - HTML table
    """

    if not rows:
        return "<p style='margin-left: 20px;'>No resources found.</p>"

    html = []
    html.append("""
        <table class="report-table sortable">
          <thead>
            <tr>
    """)

    # Table header
    for _, label in columns:
        html.append(f"<th>{label}</th>")
    html.append("</tr></thead><tbody>")

    # Sort rows safely on the first column
    first_col_field = columns[0][0] if columns else ""
    rows_sorted = sorted(rows, key=lambda r: str(r.get(first_col_field, "")).lower())

    # Table rows
    for row in rows_sorted:
        html.append("<tr>")
        for field, _ in columns:
            value = row.get(field, "")

            # Handle missing or None values
            if value is None:
                value = ""

            # Convert any non-string to string
            value = str(value)

            # Highlight 'state' column
            if field == "state":
                val_upper = value.upper()
                if val_upper in ("ENABLED", "ACTIVE", "RUNNING", "READY"):
                    value = f"<span class='state-green'>{value}</span>"
                elif val_upper in ("DISABLED", "INACTIVE", "DELETING", "RESTORING"):
                    value = f"<span class='state-orange'>{value}</span>"
                elif val_upper in ("FAILED"):
                    value = f"<span class='state-red'>{value}</span>"
                elif value == "":
                    value = "<span class='state-gray'>—</span>"
                else:
                    value = f"<span class='state-gray'>{value}</span>"

            html.append(f"<td>{value}</td>")
        html.append("</tr>")

    html.append("</tbody></table>")
    return "\n".join(html)