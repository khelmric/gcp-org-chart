# GCP Org Chart Viewer

Web app that visualizes Google Cloud resource hierarchy (organization → folders → projects) using the Cloud Asset Inventory API and an interactive Org Chart.

## Features
- Search by resource ID (organization, folder, or project).
- Interactive org chart with focus, delete, collapse, and restore actions.
- Hide/show nodes, undo/redo actions.
- Save chart as PNG.
- Light/dark mode toggle.

## Prerequisites
- Python 3.11+
- Google Cloud SDK (gcloud)
- Access to the Cloud Asset Inventory API in your project

## Setup
1. Install dependencies:
	pip install -r requirements.txt
2. Authenticate:
	gcloud auth login
	gcloud auth application-default login

## Run locally
python main.py

Open http://localhost:8080

## Run from Cloud Shell by using a Tutorial
[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.png)](https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/khelmric/gcp-org-chart&cloudshell_tutorial=tutorial.md)

## Usage
Enter a resource ID (organization ID, folder ID, or project ID) and press Enter. The hierarchy is loaded and rendered in the chart.

## Deploy to App Engine (Python 3.11)
This repo includes an app.yaml configured for Gunicorn.

1. Create the App Engine app (once):
	gcloud app create --region=europe-west3
2. Deploy:
	gcloud app deploy

## Notes
- The Org Chart uses the Cloud Asset Inventory API (searchAllResources). Ensure the caller has permissions for the resource scope.

## License
See LICENSE.
