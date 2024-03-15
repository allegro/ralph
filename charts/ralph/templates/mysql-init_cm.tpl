---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-init
data:
  init.sql: |-
    USE `mysql`;
    CREATE database `{{ .Values.mysql.database }}` default character set 'utf8';
    CREATE USER '{{ .Values.mysql.username }}'@'%' IDENTIFIED BY '{{ .Values.mysql.password }}';
    GRANT ALL PRIVILEGES ON  `{{ .Values.mysql.database }}`.* TO '{{ .Values.mysql.username }}'@'%';