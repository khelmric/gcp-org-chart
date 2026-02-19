# auth_tools.py

import google.auth
import google.auth.transport.requests
import requests

def get_authenticated_account():
    credentials, project_id = google.auth.default()
    account_info = None

    if hasattr(credentials, "service_account_email"):  
        # Service account (App Engine, Cloud Run, etc.)
        account_info = credentials.service_account_email
    else:
        # Likely a gcloud user account
        try:
            credentials.refresh(google.auth.transport.requests.Request())
            token = credentials.token
            # Call the OIDC userinfo endpoint to get the email
            resp = requests.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.ok:
                account_info = resp.json().get("email")
        except:
            account_info = "none"

    return account_info, project_id