{{ if .Values.redis.kubedb }}
---
apiVersion: kubedb.com/v1alpha2
kind: Redis
metadata:
  name: redis
spec:
  version: 6.0.6
  storageType: Durable
  storage:
    accessModes:
    - ReadWriteOnce
    resources:
      requests:
        storage: 1Gi
{{ end}}