#!/bin/bash

# Retell Chat Widget - tmux Session Manager
# This script sets up persistent tmux sessions for the server and ngrok

set -e

PROJECT_DIR="/Users/nuggylover1210/Projects/Alchemical AI/Helpware"
SESSION_PREFIX="retell"

echo "🚀 Setting up Retell Chat Widget tmux sessions..."

# Function to check if a tmux session exists
session_exists() {
    tmux has-session -t "$1" 2>/dev/null
}

# Function to create or attach to session
create_or_attach() {
    local session_name="$1"
    local command="$2"
    local description="$3"
    
    if session_exists "$session_name"; then
        echo "✅ Session '$session_name' already exists"
    else
        echo "🆕 Creating session '$session_name' for $description"
        tmux new-session -d -s "$session_name" -c "$PROJECT_DIR"
        tmux send-keys -t "$session_name" "$command" Enter
        sleep 2
    fi
}

# Check if processes are already running
SERVER_PID=$(lsof -ti:8000 2>/dev/null || echo "")
NGROK_PID=$(pgrep -f "ngrok http 8000" 2>/dev/null || echo "")

if [[ -n "$SERVER_PID" && -n "$NGROK_PID" ]]; then
    echo "⚠️  Processes already running:"
    echo "   Server PID: $SERVER_PID"
    echo "   ngrok PID: $NGROK_PID"
    echo ""
    echo "🔄 Moving existing processes to tmux sessions..."
    
    # Create tmux sessions and move existing processes
    if ! session_exists "${SESSION_PREFIX}-server"; then
        tmux new-session -d -s "${SESSION_PREFIX}-server" -c "$PROJECT_DIR"
        echo "📦 Created tmux session for existing server process"
    fi
    
    if ! session_exists "${SESSION_PREFIX}-ngrok"; then
        tmux new-session -d -s "${SESSION_PREFIX}-ngrok" -c "$PROJECT_DIR"
        echo "🌐 Created tmux session for existing ngrok process"
    fi
    
else
    echo "🆕 Starting fresh processes in tmux..."
    
    # Kill any existing processes first
    if [[ -n "$SERVER_PID" ]]; then
        echo "🛑 Stopping existing server (PID: $SERVER_PID)"
        kill "$SERVER_PID" 2>/dev/null || true
        sleep 2
    fi
    
    if [[ -n "$NGROK_PID" ]]; then
        echo "🛑 Stopping existing ngrok (PID: $NGROK_PID)"
        kill "$NGROK_PID" 2>/dev/null || true
        sleep 2
    fi
    
    # Start server in tmux
    create_or_attach "${SESSION_PREFIX}-server" "python3 server.py" "Python development server"
    
    # Wait for server to start
    echo "⏳ Waiting for server to start..."
    sleep 3
    
    # Start ngrok in tmux
    create_or_attach "${SESSION_PREFIX}-ngrok" "ngrok http 8000 --log=stdout" "ngrok tunnel"
    
    # Wait for ngrok to establish tunnel
    echo "⏳ Waiting for ngrok tunnel to establish..."
    sleep 5
fi

# Get current ngrok URL
echo ""
echo "🔍 Getting current ngrok URL..."
NGROK_URL=""
for i in {1..10}; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data['tunnels']:
        print(data['tunnels'][0]['public_url'])
    else:
        print('')
except:
    print('')
" 2>/dev/null || echo "")
    
    if [[ -n "$NGROK_URL" ]]; then
        break
    fi
    echo "   Attempt $i/10: Waiting for ngrok API..."
    sleep 2
done

# Display status
echo ""
echo "🎉 tmux Sessions Ready!"
echo "======================="
echo ""

# List tmux sessions
echo "📋 Active tmux sessions:"
tmux list-sessions | grep "$SESSION_PREFIX" || echo "   No Retell sessions found"
echo ""

if [[ -n "$NGROK_URL" ]]; then
    echo "🌐 Current URLs:"
    echo "   ⭐ Seamless Widget: $NGROK_URL/retell-seamless.html"
    echo "   📱 ChatDash Optimized: $NGROK_URL/retell-chatdash-optimized.html"
    echo "   🔧 Original Branded: $NGROK_URL/retell-inline-branded.html"
    echo ""
    echo "📋 Quick Commands:"
    echo "   Get URL: curl -s http://localhost:4040/api/tunnels | python3 -c \"import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])\""
    echo "   Test: curl -I $NGROK_URL/retell-seamless.html"
else
    echo "⚠️  Could not retrieve ngrok URL. Check if ngrok is running:"
    echo "   curl -s http://localhost:4040/api/tunnels"
fi

echo ""
echo "🔧 tmux Management Commands:"
echo "   List sessions:    tmux list-sessions"
echo "   Attach to server: tmux attach-session -t ${SESSION_PREFIX}-server"
echo "   Attach to ngrok:  tmux attach-session -t ${SESSION_PREFIX}-ngrok"
echo "   Kill all:        tmux kill-session -t ${SESSION_PREFIX}-server && tmux kill-session -t ${SESSION_PREFIX}-ngrok"
echo ""
echo "💡 Tip: Use Ctrl+B, then D to detach from a tmux session"
echo "🔄 Run this script again anytime to check status or recreate sessions"
