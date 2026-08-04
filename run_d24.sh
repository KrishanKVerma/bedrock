#!/bin/bash
# One condition per invocation. Usage: ./run_d24.sh dom_drift
export BEDROCK_PROVIDER=groq
export PYTHONUNBUFFERED=1
mkdir -p logs
python -m harness.sweep "$1" 20 2>&1 | tee "logs/d24_$1.log"