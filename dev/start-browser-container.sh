#!/bin/bash
set -e

IMAGE="zenika/alpine-chrome:latest"
CONTAINER_NAME="headless-chrome"
PORT=9222

# 如果已有同名容器，先删除
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
  docker rm -f $CONTAINER_NAME >/dev/null 2>&1 || true
fi

echo "Starting headless Chrome on port $PORT..."

docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:9222 \
  $IMAGE \
  chromium-browser \
  --headless \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --no-sandbox

echo "Headless Chrome is running."
echo "DevTools Protocol endpoint: http://localhost:$PORT/json/version"
