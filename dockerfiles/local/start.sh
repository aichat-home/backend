#!/bin/bash

python bot.py &
BOT_PID=$!

uvicorn api.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

function shutdown {
    kill $BOT_PID $UVICORN_PID
    wait $BOT_PID $UVICORN_PID
}

trap shutdown SIGINT SIGTERM

wait $BOT_PID $UVICORN_PID
