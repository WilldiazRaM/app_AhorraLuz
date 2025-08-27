cat > build.sh << 'EOF'
#!/usr/bin/env bash
set -o errexit

echo "=== [1/4] Installing dependencies ==="
pip install -r requirements.txt

echo "=== [2/4] Collecting static files ==="
python manage.py collectstatic --no-input || { echo "Collectstatic failed"; exit 1; }

echo "=== [3/4] Applying migrations ==="
python manage.py migrate || { echo "Migrations failed"; exit 1; }

echo "=== [4/4] Build completed successfully ==="
EOF

chmod a+x build.sh
git update-index --chmod=+x build.sh
git add build.sh
git commit -m "Add debug logs to build.sh"
git push origin main
