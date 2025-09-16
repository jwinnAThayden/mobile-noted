@echo off
echo Testing super simple Docker build...

docker build -f Dockerfile.simple -t mobile-noted-simple . && docker run --rm mobile-noted-simple

pause