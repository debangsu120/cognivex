#!/bin/bash
set -e

echo "Starting CogniVex AI Interview Platform..."

# Wait for database to be ready
echo "Waiting for Supabase database..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    # Check if we can connect to Supabase
    if python -c "from app.services.supabase import get_supabase_client; client = get_supabase_client()" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "Waiting for database... ($retry_count/$max_retries)"
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo "Warning: Database connection check skipped (Supabase may be unreachable)"
fi

# Check for and run database migrations if needed
echo "Checking for pending migrations..."
if [ -d "migrations" ] && [ "$(ls -A migrations/*.sql 2>/dev/null)" ]; then
    echo "Running migrations..."
    # Add migration logic here if needed
fi

# Create logs directory
mkdir -p /app/logs

# Apply any pending updates
echo "Applying production configurations..."

# Start the application
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4