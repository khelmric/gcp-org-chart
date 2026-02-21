# GCP Org Chart Viewer - Cloud Shell Tutorial

## Overview
This tutorial prepares your Cloud Shell environment and launches the GCP Org Chart Viewer web app.

**Time to complete**: <walkthrough-tutorial-duration duration="8"></walkthrough-tutorial-duration>

## Prerequisites
1. **Select a Google Cloud project**:
   <walkthrough-project-setup></walkthrough-project-setup>

2. **Enable the Cloud Asset Inventory API**:
   <walkthrough-enable-apis apis="cloudasset.googleapis.com"></walkthrough-enable-apis>

3. **Required IAM roles**:
   Your user should have:
   - `roles/resourcemanager.organizationViewer`
   - `roles/resourcemanager.folderViewer`
   - `roles/resourcemanager.projectViewer`

   If needed, open IAM to grant permissions:
   [Open IAM Page](https://console.cloud.google.com/iam-admin/iam)

Click **Start** to proceed.

## Prepare the environment
Run the following commands in Cloud Shell:

Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

Authenticate with Application Default Credentials:

```bash
gcloud auth application-default login
```

Set the ADC quota project to the selected project:

```bash
gcloud auth application-default set-quota-project <walkthrough-project-id/>
```

Click **Next** to proceed.

## Start the web app
Run the app:

```bash
python3 main.py
```

Open the web preview:

<walkthrough-web-preview></walkthrough-web-preview>

In the app, enter an Organization, Folder, or Project ID and press **Enter** to load the hierarchy.

## Congratulations

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You’re all set! If you run into issues, verify:
- The API is enabled
- Your IAM roles are granted
- ADC login is completed
