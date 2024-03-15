---
apiVersion: v1
kind: Secret
metadata:
  name: mysql
type: Opaque
data:
  username:  {{ .Values.mysql.username | b64enc }}
  password: {{ .Values.mysql.password | b64enc }}
  MYSQL_USER: {{ .Values.mysql.username | b64enc }}
  MYSQL_PASSWORD: {{ .Values.mysql.password | b64enc }}
  MYSQL_HOST: {{ .Values.mysql.host | b64enc }}
  MYSQL_PORT: {{ .Values.mysql.port | b64enc }}
  MYSQL_DATABASE: {{ .Values.mysql.database | b64enc }}
  MYSQL_SSL: {{ .Values.mysql.ssl | b64enc }}
