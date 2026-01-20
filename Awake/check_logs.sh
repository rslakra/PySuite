#!/bin/bash
echo "Checking Awake logs..."
echo "Log file: ~/Library/Logs/Awake.log"
echo ""
if [ -f ~/Library/Logs/Awake.log ]; then
    echo "=== Last 20 lines of log ==="
    tail -20 ~/Library/Logs/Awake.log
else
    echo "Log file not found. App may not have started."
fi
