# increase the number of pods per node:
# --: kubectl set env daemonset aws-node -n kube-system MAX_PODS=110
# --: kubectl rollout restart daemonset aws-node -n kube-system

# -- to build all images,delete all the images and containers in docker first, 
# ---   then set the env variables in the .env file (under autogpt_platform) using:
# Get-Content .env | ForEach-Object { if ($_ -match '^(.*?)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') } }
# ---   then cd autogpt_platform\ then docker compose up # to build all images
# -- then update each image version in this file (in the docker tag commands below ) and in all yaml files under _eks\supbase 
# --      to each version from autogpt_platform/db/docker/docker-compose.yml


aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 582822331796.dkr.ecr.us-east-1.amazonaws.com


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

kubectl get pvc -n autogpt --no-headers | ForEach-Object { kubectl delete pvc -n autogpt --force $_.Split(" ")[0] }
kubectl get pv -n autogpt --no-headers | ForEach-Object { kubectl delete pv -n autogpt --force $_.Split(" ")[0] }

# do not run this unless you want to recreate all LBs and DNS
# kubectl get service -n autogpt --no-headers | ForEach-Object { kubectl delete service -n autogpt --force $_.Split(" ")[0] }

### ----------

# copy files
kubectl apply -f .\pvc.yaml
kubectl apply -f .\manager.yaml
# do not execute the below until manager is running
# login to manager: kubectl exec -n autogpt manager -it -- bash   
kubectl -n autogpt exec -it manager -- rm -R /data/db0/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/db4/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/dbconfig/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/vector0/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/function0/lost+found
kubectl -n autogpt exec -it manager -- rm -R /data/kong0/lost+found

# db
kubectl -n autogpt exec -it manager -- mkdir -p /data/db0/migrations/
kubectl -n autogpt exec -it manager -- mkdir -p /data/db0/init-scripts/
kubectl -n autogpt cp ../db/docker/volumes/db/realtime.sql manager:/data/db0/migrations/99-realtime.sql
kubectl -n autogpt cp ../db/docker/volumes/db/webhooks.sql manager:/data/db0/init-scripts/98-webhooks.sql
kubectl -n autogpt cp ../db/docker/volumes/db/roles.sql manager:/data/db0/init-scripts/99-roles.sql
kubectl -n autogpt cp ../db/docker/volumes/db/jwt.sql manager:/data/db0/init-scripts/99-jwt.sql
kubectl -n autogpt cp ../db/docker/volumes/db/_supabase.sql manager:/data/db0/migrations/97-_supabase.sql
kubectl -n autogpt cp ../db/docker/volumes/db/logs.sql manager:/data/db0/migrations/99-logs.sql
kubectl -n autogpt cp ../db/docker/volumes/db/pooler.sql manager:/data/db0/migrations/99-pooler.sql
kubectl -n autogpt cp ../db/docker/volumes/supabase-config/read-replica.conf manager:/data/dbconfig/
kubectl -n autogpt cp ../db/docker/volumes/supabase-config/supautils.conf manager:/data/dbconfig/
kubectl -n autogpt cp ../db/docker/volumes/supabase-config/wal-g.conf manager:/data/dbconfig/
#kubectl -n autogpt cp ../db/docker/volumes/postgresql/postgresql.conf manager:/data/dbconfig/
#kubectl -n autogpt cp ../db/docker/volumes/db/data manager:/data/db4/
#kubectl -n autogpt exec -it manager -- bash -c "mv /data/db4/data/* /data/db4/"
#kubectl -n autogpt exec -it manager -- bash -c "chmod -R 777 /data/db4/"

#vector
kubectl -n autogpt cp ../db/docker/volumes/logs/vector.yml manager:/data/vector0/vector.yml
# functions
kubectl -n autogpt cp ../db/docker/volumes/functions/ manager:/data/function0/
kubectl -n autogpt exec -it manager -- bash -c "mv /data/function0/functions/* /data/function0/"
kubectl -n autogpt exec -it manager -- bash -c "rm -R /data/function0/functions"
#kong
kubectl -n autogpt cp ../db/docker/volumes/api/kong.yml manager:/data/kong0/temp.yml

# then delete the manager pod
kubectl -n autogpt delete pods manager --force
### ----------

# supbase -- db
kubectl apply -f .\supbase\0-db.yaml
# supbase -- auth
kubectl apply -f .\supbase\1-gotrue.yaml
# supbase -- realtime
kubectl apply -f .\supbase\1-realtime.yaml
# supbase -- postgrest
kubectl apply -f .\supbase\1-rest.yaml
# supbase -- meta
kubectl apply -f .\supbase\2-meta.yaml
# supbase -- storage
kubectl apply -f .\supbase\2-storage.yaml
# supbase -- kong
kubectl apply -f .\supbase\3-kong.yaml
# supbase -- analytics
kubectl apply -f .\supbase\4-analytics.yaml
# supbase -- functions
kubectl apply -f .\supbase\4-functions.yaml
# supbase -- imgproxy
kubectl apply -f .\supbase\4-imgproxy.yaml
# supbase -- studio
kubectl apply -f .\supbase\4-studio.yaml
# supbase -- vector
kubectl apply -f .\supbase\4-vector.yaml

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
cd ../
docker compose build migrate
docker tag autogpt_platform-migrate 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/migrate
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/migrate:latest
kubectl apply -f _eks\autogpt\0-migrate.yaml
kubectl apply -f _eks\autogpt\0-redis.yaml
kubectl apply -f _eks\autogpt\0-rabbitmq.yaml

cd ../
docker build -t autogpt-backend .
docker tag autogpt-backend 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/backend
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/backend:latest
kubectl apply -f autogpt_platform\_eks\autogpt\1-backend.yaml

# docker tag autogpt_platform-executor 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/executor
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/executor:latest

# docker tag autogpt_platform-rest_server 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/rest-server
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/rest-server:latest

# docker tag autogpt_platform-websocket_server 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/websocket
# docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/websocket:latest


# kubectl apply -f .\autogpt\executor.yaml
# kubectl apply -f .\autogpt\rest-server.yaml
# kubectl apply -f .\autogpt\websocket.yaml

# ===================
# to deploy frontend
# ===================
# on autogpt folder (just above autogpt_platform), run:
# docker build -t autogpt-frontend -f .\autogpt_platform\frontend\Dockerfile  .
# also make sure autogpt_platform/frontend/.env.local is configured properly as all env variables are stored there. if anything changes, rebuild the image first.
docker tag autogpt-frontend 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/frontend
docker push 582822331796.dkr.ecr.us-east-1.amazonaws.com/autogpt/platform/frontend:latest
kubectl apply -f autogpt_platform\_eks\autogpt\9-frontend.yaml