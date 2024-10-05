#!/bin/sh

python bot.py &

# Start the Uvicorn server
uvicorn main:app --host 0.0.0.0 --port 8000
