#!/bin/bash
pip install -e .
cd backend2
python -m uvicorn backend2.app:app --host 0.0.0.0 --port $PORT 
