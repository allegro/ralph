{{ if .Values.mysql.kubedb }}
---
apiVersion: kubedb.com/v1alpha2
kind: MySQL
metadata:
  name: mysql
spec:
  version: "5.7.33-v1"
  storageType: {{ .Values.mysql.storageType }}
  storage:
    storageClassName: {{ .Values.mysql.storageClassName }}
    accessModes:
    - ReadWriteOnce
    resources:
      requests:
        storage: 10Gi
  terminationPolicy: {{ .Values.mysql.terminationPolicy }}
  authSecret:
    name: mysql
  init:
    script:
      configMap:
        name: mysql-init
{{ end }}