#!/bin/bash

# WeeklyRoulette Bot - Fly.io Deployment Script
# Usage: ./deploy.sh [app-name]

set -e

APP_NAME=${1:-"weeklyroulette-bot"}
REGION=${FLY_REGION:-"fra"}

echo "🚀 Deploying WeeklyRoulette Bot to Fly.io"
echo "App name: $APP_NAME"
echo "Region: $REGION"

# Check if flyctl is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Install it first:"
    echo "   https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if logged in
if ! fly auth whoami &> /dev/null; then
    echo "🔐 Logging into Fly.io..."
    fly auth login
fi

# Update app name in fly.toml if provided
if [ "$APP_NAME" != "weeklyroulette-bot" ]; then
    sed -i.bak "s/app = \"weeklyroulette-bot\"/app = \"$APP_NAME\"/" fly.toml
    echo "✏️  Updated app name in fly.toml"
fi

# Check if app exists, create if not
if ! fly apps list | grep -q "^$APP_NAME"; then
    echo "📱 Creating new app: $APP_NAME"
    fly apps create "$APP_NAME"
else
    echo "✅ App $APP_NAME already exists"
fi

# Check if volume exists, create if not
if ! fly volumes list -a "$APP_NAME" | grep -q "weeklyroulette_data"; then
    echo "💾 Creating volume for database..."
    fly volumes create weeklyroulette_data --region "$REGION" --size 1 -a "$APP_NAME"
else
    echo "✅ Volume already exists"
fi

# Check if secrets are set
echo "🔑 Checking required secrets..."
MISSING_SECRETS=""

if ! fly secrets list -a "$APP_NAME" | grep -q "SLACK_BOT_TOKEN"; then
    MISSING_SECRETS="$MISSING_SECRETS SLACK_BOT_TOKEN"
fi

if ! fly secrets list -a "$APP_NAME" | grep -q "SLACK_APP_TOKEN"; then
    MISSING_SECRETS="$MISSING_SECRETS SLACK_APP_TOKEN"
fi

if ! fly secrets list -a "$APP_NAME" | grep -q "SLACK_SIGNING_SECRET"; then
    MISSING_SECRETS="$MISSING_SECRETS SLACK_SIGNING_SECRET"
fi

if [ -n "$MISSING_SECRETS" ]; then
    echo "❌ Missing required secrets:$MISSING_SECRETS"
    echo ""
    echo "Set them with:"
    for secret in $MISSING_SECRETS; do
        echo "  fly secrets set $secret=your-value -a $APP_NAME"
    done
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ All required secrets are set"
fi

# Deploy
echo "🏗️  Deploying application..."
fly deploy -a "$APP_NAME"

# Show status
echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📊 App status:"
fly status -a "$APP_NAME"

echo ""
echo "📝 Useful commands:"
echo "  View logs:    fly logs -a $APP_NAME"
echo "  Open dashboard: fly dashboard -a $APP_NAME"
echo "  SSH access:   fly ssh console -a $APP_NAME"
echo ""
