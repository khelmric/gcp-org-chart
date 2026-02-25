# GCP Org Chart Viewer

Web app that visualizes Google Cloud resource hierarchy (organization → folders → projects) using the Cloud Asset Inventory API and an interactive Org Chart.

## Features
- Zoom in/out with the mouse wheel.
- Pan the chart with drag-and-drop (left click + hold).
- Collapse/expand nodes with double click.
- Search for any content using the Search field. The search function works in tooltips too where the resource create_date is placed (e.g. search for resources created on the 2025-12-12).
- Focus on a child resource with the **Focus** button.
- Hide resources with the **Hide** button.
- Delete a resource and all children with the **Delete** button.
- Undo/redo actions with the **↺** and **↻** buttons.
- Restore the initial view with the **Reset all** button.
- Switch between light and dark mode.
- Save the chart as PNG.

## Prerequisites
- Python 3.11+
- Google Cloud SDK (gcloud)
- Access to the Cloud Asset Inventory API in your project

## Setup
1. Install dependencies:
	pip install -r requirements.txt
2. Authenticate & set quota project:
	gcloud auth application-default login
    gcloud auth application-default set-quota-project [PROJECT_ID]

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

## Screenshots

### Light-mode
![Alt text](examples/light-mode.png?raw=true "Light-mode")

### Dark-mode
![Alt text](examples/dark-mode.png?raw=true "Dark-mode")

### Demo
![Alt text](examples/demo.gif?raw=true "Demo")

## Notes
- The Org Chart uses the Cloud Asset Inventory API (searchAllResources). Ensure the caller has permissions for the resource scope.

## Buy me a coffee
If this project helps you, you can support it here:
https://buymeacoffee.com/khelmric

## License
See LICENSE.
