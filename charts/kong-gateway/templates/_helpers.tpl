{{/*
Create KOPF cli option for the comma seperated list of namespaces in monitoredNamespaces:
"<ns1>,<ns1>,...<nsN>"-> "-n <ns1> -n <ns2> ... -n <nsN>" 
*/}}
{{- define "api-operator-kong.monitoredNamespacesCLIOpts" -}}
{{- printf "-n %s" .Values.deployment.monitoredNamespaces | replace "," " -n " }}
{{- end -}}
