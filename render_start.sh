#!/bin/bash
cd backend2
python -m uvicorn app:app --host 0.0.0.0 --port $PORT 