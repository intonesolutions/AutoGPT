aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 582822331796.dkr.ecr.us-east-1.amazonaws.com

docker build -t autogpt-backend .
docker tag autogpt-backend 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/backend
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/backend:latest
kubectl apply -f autogpt_platform\_eks\autogpt\1-backend.yaml
