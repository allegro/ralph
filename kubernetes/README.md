Note: this does not work right out of the box yet
 - required: manual run of `/var/local/ralph/docker-entrypoint.sh init` (maybe use initContainer)
 - required: manual run of `ralphctl collectstatic` to deploy static files to shared volume for nginx (maybe use lifecycle postStart

kubectl create namespace ralph
kubectl apply -f . -n ralph
