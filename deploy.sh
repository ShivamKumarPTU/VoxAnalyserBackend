#!/bin/bash

# Set your project ID
PROJECT_ID="YOUR_PROJECT_ID"
REGION="asia-south1"  # Mumbai, India 🇮🇳
SERVICE_NAME="emotion-analyzer"

# Set project
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and deploy
echo "🚀 Building container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "🚀 Deploying to Cloud Run in $REGION..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --concurrency 1 \
  --max-instances 5 \
  --min-instances 0 \
  --port 8080 \
  --allow-unauthenticated \
  --cpu-boost \
  --execution-environment gen2

echo "✅ Deployment complete!"
echo "🌍 Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"