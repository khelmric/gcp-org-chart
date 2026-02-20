# common.py

resource_type_icons = {
    "project": '<img src="/static/img/project.png" width="25" height="25" style="display:inline-block;vertical-align:middle">',
    "folder": '<img src="/static/img/folder.png" width="25" height="25" style="display:inline-block;vertical-align:middle">',
    "organization": '<img src="/static/img/organization.png" width="30" height="30" style="display:inline-block;vertical-align:middle">'
}

resource_type_icons_small = {
    "project": '<img src="/static/img/project.png" width="15" height="15" style="display:inline-block;vertical-align:middle">',
    "folder": '<img src="/static/img/folder.png" width="15" height="15" style="display:inline-block;vertical-align:middle">',
    "organization": '<img src="/static/img/organization.png" width="20" height="20" style="display:inline-block;vertical-align:middle">'
}

def html_display_labels(labels_list):
    labels_html = "".join(
        f"<span class='label'>{k}: {v}</span>"
        for k, v in labels_list.items()
    )
    return labels_html

def html_display_tags(tags_list):
    tags_html = "".join(
        f"<span class='tag'>{tag}</span>"
        for tag in tags_list
    )
    return tags_html

def html_display_list(list):
    list_html = "".join(
        f"<span class='common-item'>{item}</span>"
        for item in list
    )
    return list_html

def get_kms_main_data(kms_key_raw):
    parts = kms_key_raw.split('/')
    keyring = parts[parts.index("keyRings") + 1]
    key = parts[parts.index("cryptoKeys") + 1]
    result = f"{keyring}/{key}"
    return result