#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Translation System Debug Script${NC}"
echo "=================================="

# Check Redis
echo -e "\n${YELLOW}1. Checking Redis...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
    
    # Check queues
    echo -e "\n${YELLOW}   Queue lengths:${NC}"
    for queue in extraction translation reconstruction; do
        length=$(redis-cli llen $queue 2>/dev/null || echo "0")
        echo "   - $queue: $length items"
    done
else
    echo -e "${RED}✗ Redis is not running${NC}"
fi

# Check Celery Worker
echo -e "\n${YELLOW}2. Checking Celery Worker...${NC}"
if celery -A celery_app inspect active_queues 2>/dev/null | grep -q "celery\|extraction\|translation\|reconstruction"; then
    echo -e "${GREEN}✓ Worker is running${NC}"
    
    # Show active queues
    echo -e "\n${YELLOW}   Active queues:${NC}"
    celery -A celery_app inspect active_queues 2>/dev/null | grep -A 10 "queues" | head -15
else
    echo -e "${RED}✗ Worker is not running or not listening to correct queues${NC}"
fi

# Check FastAPI
echo -e "\n${YELLOW}3. Checking FastAPI...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ FastAPI is running on port 8000${NC}"
else
    echo -e "${RED}✗ FastAPI is not running${NC}"
fi

# Check Ngrok
echo -e "\n${YELLOW}4. Checking Ngrok...${NC}"
if pgrep -f ngrok > /dev/null; then
    echo -e "${GREEN}✓ Ngrok is running${NC}"
    
    # Try to get URL
    ngrok_url=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*' | cut -d'"' -f4 | head -1)
    if [ ! -z "$ngrok_url" ]; then
        echo -e "   URL: ${GREEN}$ngrok_url${NC}"
    fi
else
    echo -e "${RED}✗ Ngrok is not running${NC}"
fi

# Check Frontend
echo -e "\n${YELLOW}5. Checking Frontend...${NC}"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running on port 3000${NC}"
    
    # Check .env.local
    if [ -f ~/prismy-minimal/.env.local ]; then
        api_url=$(grep NEXT_PUBLIC_API_URL ~/prismy-minimal/.env.local | cut -d'=' -f2)
        echo -e "   API URL: ${GREEN}$api_url${NC}"
    fi
else
    echo -e "${RED}✗ Frontend is not running${NC}"
fi

echo -e "\n${YELLOW}=================================="
echo -e "📋 Summary:${NC}"

# Quick health check
all_good=true
[ ! -z "$(redis-cli ping 2>/dev/null)" ] || all_good=false
celery -A celery_app inspect active_queues 2>/dev/null | grep -q "translation" || all_good=false
curl -s http://localhost:8000/health > /dev/null 2>&1 || all_good=false

if [ "$all_good" = true ]; then
    echo -e "${GREEN}✅ All core services are running!${NC}"
else
    echo -e "${RED}❌ Some services need attention${NC}"
fi

# Test translation if requested
if [ "$1" = "test" ]; then
    echo -e "\n${YELLOW}🧪 Running translation test...${NC}"
    
    # Create a simple test PDF
    echo "Creating test PDF..."
    echo "Hello World" | enscript -B -o - | ps2pdf - test.pdf
    
    # Upload and translate
    echo "Uploading to API..."
    response=$(curl -s -X POST http://localhost:8000/api/v1/large/translate \
        -F "file=@test.pdf" \
        -F "source_language=en" \
        -F "target_language=es")
    
    job_id=$(echo $response | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)
    
    if [ ! -z "$job_id" ]; then
        echo -e "${GREEN}✓ Job created: $job_id${NC}"
        
        # Check status
        echo "Checking status..."
        for i in {1..10}; do
            status=$(curl -s http://localhost:8000/api/v1/large/status/$job_id | grep -o '"status":"[^"]*' | cut -d'"' -f4)
            progress=$(curl -s http://localhost:8000/api/v1/large/status/$job_id | grep -o '"progress":[0-9]*' | cut -d':' -f2)
            echo "   Status: $status (${progress}%)"
            
            if [ "$status" = "completed" ]; then
                echo -e "${GREEN}✅ Translation completed!${NC}"
                break
            elif [ "$status" = "failed" ]; then
                echo -e "${RED}❌ Translation failed${NC}"
                break
            fi
            
            sleep 2
        done
    else
        echo -e "${RED}✗ Failed to create job${NC}"
    fi
    
    # Cleanup
    rm -f test.pdf
fi

echo -e "\n💡 Tip: Run '$0 test' to run a full translation test"