
# Prerequistes

 - Kubernetes cluster >= v1.19.11
 - Helm 3 
Find instructions here: https://helm.sh/docs/intro/install/)
 - KubeDB Community Edition (optional but easier)
Find instructions here: 
https://kubedb.com/docs/v2021.06.23/setup/install/community/

# How to install this Helm chart

## Edit values in values.yaml

Default should be fine except the ingress hostname

## Install the chart & Configure database

```
helm install ralph charts/ralph # from ralph git root directory
kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
mysql-0                  1/1     Running   0          104s
ralph-58f4968585-f7cm7   2/2     Running   0          105s  <------ralph pod
redis-0                  1/1     Running   0          104s
```

Get the ralph pod name (here ralph-58f4968585-f7cm7) and start database migration:
```
kubectl exec -ti ralph-58f4968585-f7cm7 -- ralph migrate
```

Then, create a superuser:
```
kubectl exec -ti ralph-58f4968585-f7cm7 -- ralph createsuperuser
```

