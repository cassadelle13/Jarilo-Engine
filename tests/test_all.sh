#!/bin/bash
echo "Rebuilding brain..."
docker-compose build brain
echo "Starting services..."
docker-compose up -d
echo "Waiting 3 seconds..."
sleep 3
echo "Testing..."
python test_code_execution.py