# increase the number of pods per node:
# --: kubectl set env daemonset aws-node -n kube-system MAX_PODS=110
# --: kubectl rollout restart daemonset aws-node -n kube-system

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 582822331796.dkr.ecr.us-east-1.amazonaws.com

aws ecr create-repository --repository-name autogpt/supbase/vector
aws ecr create-repository --repository-name autogpt/supbase/db
aws ecr create-repository --repository-name autogpt/supbase/logflare
aws ecr create-repository --repository-name autogpt/supbase/gotrue
aws ecr create-repository --repository-name autogpt/supbase/postgres-meta
aws ecr create-repository --repository-name autogpt/supbase/realtime
aws ecr create-repository --repository-name autogpt/supbase/postgrest/postgrest
aws ecr create-repository --repository-name autogpt/supabase/studio
aws ecr create-repository --repository-name autogpt/supabase/edge-runtime
aws ecr create-repository --repository-name autogpt/supabase/darthsim/imgproxy
aws ecr create-repository --repository-name autogpt/supabase/storage-api
aws ecr create-repository --repository-name autogpt/supabase/kong
aws ecr create-repository --repository-name autogpt/platform/executor
aws ecr create-repository --repository-name autogpt/platform/rest-server
aws ecr create-repository --repository-name autogpt/platform/websocket
aws ecr create-repository --repository-name autogpt/platform/redis
aws ecr create-repository --repository-name autogpt/platform/rabbitmq
aws ecr create-repository --repository-name autogpt/platform/migrate
aws ecr create-repository --repository-name autogpt/platform/backend
aws ecr create-repository --repository-name autogpt/platform/frontend
kubectl create namespace autogpt


### delete all everything
kubectl get pods -n autogpt --no-headers | ForEach-Object { kubectl delete pods -n autogpt --force $_.Split(" ")[0] }
kubectl get deployment -n autogpt --no-headers | ForEach-Object { kubectl delete deployment -n autogpt --force $_.Split(" ")[0] }

kubectl get service -n autogpt --no-headers | ForEach-Object { kubectl delete service -n autogpt --force $_.Split(" ")[0] }

kubectl get pvc -n autogpt --no-headers | ForEach-Object { kubectl delete pvc -n autogpt --force $_.Split(" ")[0] }
kubectl get pv -n autogpt --no-headers | ForEach-Object { kubectl delete pv -n autogpt --force $_.Split(" ")[0] }
### ----------

# copy files
kubectl apply -f .\pvc.yaml
kubectl apply -f .\manager.yaml
# login to manager: kubectl exec -n autogpt manager -it -- bash   
kubectl -n autogpt exec -it manager -- rm -R /data/db0/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/db4/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/dbconfig/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/vector0/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/function0/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/kong0/lost+found
# kubectl -n autogpt exec -it manager -- mkdir -p /etc/vecto

kubectl -n autogpt cp ../supabase/docker/volumes/logs/vector.yml manager:/data/vector0/vector.yml

kubectl -n autogpt exec -it manager -- mkdir -p /data/db0/migrations/
kubectl -n autogpt exec -it manager -- mkdir -p /data/db0/init-scripts/
kubectl -n autogpt cp ../supabase/docker/volumes/db/realtime.sql manager:/data/db0/migrations/99-realtime.sql
kubectl -n autogpt cp ../supabase/docker/volumes/db/webhooks.sql manager:/data/db0/init-scripts/98-webhooks.sql
kubectl -n autogpt cp ../supabase/docker/volumes/db/roles.sql manager:/data/db0/init-scripts/roles.sql
kubectl -n autogpt cp ../supabase/docker/volumes/db/jwt.sql manager:/data/db0/init-scripts/jwt.sql
kubectl -n autogpt cp ../supabase/docker/volumes/db/logs.sql manager:/data/db0/migrations/99-logs.sql

kubectl -n autogpt cp ../supabase/docker/volumes/db/data manager:/data/db4/
kubectl -n autogpt exec -it manager -- bash -c "mv /data/db4/data/* /data/db4/"

kubectl -n autogpt cp ../supabase/docker/volumes/functions/ manager:/data/function0/
kubectl -n autogpt exec -it manager -- bash -c "mv /data/function0/functions/* /data/function0/"
kubectl -n autogpt exec -it manager -- bash -c "rm -R /data/function0/functions"

kubectl -n autogpt cp ../supabase/docker/volumes/api/kong.yml manager:/data/kong0/temp.yml

# then delete the manager pod
kubectl -n autogpt delete pods manager --force
### ----------


# supbase -- vector
docker tag timberio/vector:0.28.1-alpine 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/vector:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/vector:latest
kubectl apply -f .\supbase\vector.yaml

# supbase -- db
docker tag supabase/postgres:15.1.1.78 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/db:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/db:latest
kubectl apply -f .\supbase\db.yaml

# supbase -- analytics
docker tag supabase/logflare:1.4.0 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/logflare:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/logflare:latest
kubectl apply -f .\supbase\analytics.yaml

# supbase -- auth
docker tag supabase/gotrue:v2.158.1 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/gotrue:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/gotrue:latest
kubectl apply -f .\supbase\auth.yaml

# supbase -- meta
docker tag supabase/postgres-meta:v0.83.2 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/postgres-meta:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/postgres-meta:latest
kubectl apply -f .\supbase\meta.yaml

# supbase -- realtime
docker tag supabase/realtime:v2.30.34 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/realtime:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/realtime:latest
kubectl apply -f .\supbase\realtime.yaml

# supbase -- postgrest
docker tag postgrest/postgrest:v12.2.0 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/postgrest/postgrest:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supbase/postgrest/postgrest:latest
kubectl apply -f .\supbase\rest.yaml

# supbase -- studio
docker tag supabase/studio:20240729-ce42139 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/studio:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/studio:latest
kubectl apply -f .\supbase\studio.yaml

# supbase -- functions
docker tag supabase/edge-runtime:v1.58.2 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/edge-runtime:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/edge-runtime:latest
kubectl apply -f .\supbase\functions.yaml

# supbase -- imgproxy
docker tag darthsim/imgproxy:v3.8.0 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/darthsim/imgproxy:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/darthsim/imgproxy:latest
kubectl apply -f .\supbase\imgproxy.yaml

# supbase -- storage
docker tag supabase/storage-api:v1.10.1 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/storage-api:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/storage-api:latest
kubectl apply -f .\supbase\storage.yaml

# supbase -- kong
docker tag kong:2.8.1 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/kong:latest
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/supabase/kong:latest
kubectl apply -f .\supbase\kong.yaml

# ====================
# autogpt platform
# ====================
# instructions:
# to build backend: cd  /autoGPT (just above autogpt_platform)
# docker build -t autogpt-backend . (make sure Dockerfile ends with these lines:
									# COPY autogpt_platform/backend/.env.eks /app/autogpt_platform/backend/.env
									# RUN export $(grep -v '^#' /app/autogpt_platform/backend/.env | xargs)
									# EXPOSE 8001 8002 8003 8004 8005 8006 8007
									# CMD ["poetry", "run", "app"]
# also make sure autogpt_platform/backend/.env.eks is configured properly as all env variables are stored there. if anything changes, rebuild the image first.

docker tag autogpt-backend 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/backend
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/backend:latest
kubectl apply -f .\autogpt\1-backend.yaml

# docker tag autogpt_platform-executor 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/executor
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/executor:latest

# docker tag autogpt_platform-rest_server 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/rest-server
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/rest-server:latest

# docker tag autogpt_platform-websocket_server 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/websocket
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/websocket:latest

# docker tag redis 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/redis
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/redis:latest

# docker tag rabbitmq:management 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/rabbitmq
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/rabbitmq:latest

# docker tag autogpt_platform-migrate 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/migrate
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/migrate:latest


# kubectl apply -f .\autogpt\executor.yaml
# kubectl apply -f .\autogpt\rabbitmq.yaml
# kubectl apply -f .\autogpt\redis.yaml
# kubectl apply -f .\autogpt\rest-server.yaml
# kubectl apply -f .\autogpt\websocket.yaml
# kubectl apply -f .\autogpt\migrate.yaml

# ===================
# to deploy frontend
# ===================
# on autogpt folder (just above autogpt_platform), run:
# docker build -t autogpt-frontend -f .\autogpt_platform\frontend\Dockerfile  .
# also make sure autogpt_platform/backend/.env.eks is configured properly as all env variables are stored there. if anything changes, rebuild the image first.
docker tag autogpt-frontend 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/frontend
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/frontend:latest
kubectl apply -f .\autogpt\9-frontend.yaml