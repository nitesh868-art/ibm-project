#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static assets via WhiteNoise..."
python manage.py collectstatic --no-input

echo "==> Applying database migrations..."
python manage.py migrate --no-input

echo "==> Seeding initial curriculum, mock assessments & accounts..."
python manage.py seed_demo_data || true

echo "==> Build completed successfully!"
