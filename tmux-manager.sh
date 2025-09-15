#!/bin/bash

# Retell Chat Widget - tmux Session Manager
# Quick commands for managing tmux sessions

SESSION_PREFIX="retell"

case "$1" in
    "start")
        echo "🚀 Starting Retell tmux sessions..."
        ./start-tmux.sh
        ;;
    "status")
        echo "📋 tmux Session Status:"
        tmux list-sessions 2>/dev/null | grep "$SESSION_PREFIX" || echo "   No Retell sessions running"
        echo ""
        
        # Check if processes are running
        SERVER_PID=$(lsof -ti:8000 2>/dev/null || echo "")
        NGROK_PID=$(pgrep -f "ngrok http 8000" 2>/dev/null || echo "")
        
        if [[ -n "$SERVER_PID" ]]; then
            echo "✅ Server running (PID: $SERVER_PID)"
        else
            echo "❌ Server not running"
        fi
        
        if [[ -n "$NGROK_PID" ]]; then
            echo "✅ ngrok running (PID: $NGROK_PID)"
            
            # Get ngrok URL
            NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data['tunnels']:
        print(data['tunnels'][0]['public_url'])
except:
    pass
" 2>/dev/null || echo "")
            
            if [[ -n "$NGROK_URL" ]]; then
                echo "🌐 Current URL: $NGROK_URL"
                echo "   ⭐ Widget: $NGROK_URL/retell-seamless.html"
            fi
        else
            echo "❌ ngrok not running"
        fi
        ;;
    "attach-server")
        echo "🔗 Attaching to server session..."
        tmux attach-session -t "${SESSION_PREFIX}-server"
        ;;
    "attach-ngrok")
        echo "🔗 Attaching to ngrok session..."
        tmux attach-session -t "${SESSION_PREFIX}-ngrok"
        ;;
    "stop")
        echo "🛑 Stopping all Retell tmux sessions..."
        tmux kill-session -t "${SESSION_PREFIX}-server" 2>/dev/null || echo "   Server session not found"
        tmux kill-session -t "${SESSION_PREFIX}-ngrok" 2>/dev/null || echo "   ngrok session not found"
        echo "✅ Sessions stopped"
        ;;
    "restart")
        echo "🔄 Restarting Retell tmux sessions..."
        $0 stop
        sleep 2
        $0 start
        ;;
    "url")
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data['tunnels']:
        print(data['tunnels'][0]['public_url'])
except:
    pass
" 2>/dev/null || echo "")
        
        if [[ -n "$NGROK_URL" ]]; then
            echo "🌐 Current ngrok URL: $NGROK_URL"
            echo ""
            echo "📱 Widget URLs:"
            echo "   ⭐ Seamless:     $NGROK_URL/retell-seamless.html"
            echo "   📱 Optimized:    $NGROK_URL/retell-chatdash-optimized.html"
            echo "   🔧 Original:     $NGROK_URL/retell-inline-branded.html"
        else
            echo "❌ Could not get ngrok URL. Is ngrok running?"
        fi
        ;;
    *)
        echo "🎛️  Retell Chat Widget - tmux Manager"
        echo "======================================"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "   start          Start/setup tmux sessions"
        echo "   status         Show session and process status"
        echo "   attach-server  Attach to server session"
        echo "   attach-ngrok   Attach to ngrok session"
        echo "   stop           Stop all sessions"
        echo "   restart        Restart all sessions"
        echo "   url            Show current ngrok URLs"
        echo ""
        echo "Examples:"
        echo "   $0 start       # Set up tmux sessions"
        echo "   $0 status      # Check what's running"
        echo "   $0 url         # Get current widget URLs"
        echo ""
        echo "💡 Tip: Use Ctrl+B, then D to detach from tmux sessions"
        ;;
esac
