{{/*
build the full kong docker image name from image + version + prereleaseSuffix
*/}}
{{- define "api-operator-kong.kongopDockerimage" -}}
  {{- .Values.kongoperatorimage.kongopImage -}}:{{- .Values.kongoperatorimage.kongopVersion -}}
  {{- if .Values.kongoperatorimage.kongopPrereleaseSuffix -}}
    -{{- .Values.kongoperatorimage.kongopPrereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
overwrite kong imagePullSecret with "Always" if prereleaseSuffix is set
*/}}
{{- define "api-operator-kong.kongopImagePullPolicy" -}}
  {{- if .Values.kongoperatorimage.kongopPrereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.kongoperatorimage.pullPolicy -}}
  {{- end -}}
{{- end -}}


{{/*
Create KOPF cli option for the comma seperated list of namespaces in monitoredNamespaces:
"<ns1>,<ns1>,...<nsN>"-> "-n <ns1> -n <ns2> ... -n <nsN>" 
*/}}
{{- define "api-operator-kong.monitoredNamespacesCLIOpts" -}}
{{- printf "-n %s" .Values.deployment.monitoredNamespaces | replace "," " -n " }}
{{- end -}}
