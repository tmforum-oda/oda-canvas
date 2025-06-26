{{/*
build the full apisix docker image name from image + version + prereleaseSuffix
*/}}
{{- define "api-operator-apisix.apisixopDockerimage" -}}
  {{- .Values.apisixoperatorimage.apisixopImage -}}:{{- .Values.apisixoperatorimage.apisixopVersion -}}
  {{- if .Values.apisixoperatorimage.apisixopPrereleaseSuffix -}}
    -{{- .Values.apisixoperatorimage.apisixopPrereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
overwrite apisix imagePullSecret with "Always" if prereleaseSuffix is set
*/}}
{{- define "api-operator-apisix.apisixopImagePullPolicy" -}}
  {{- if .Values.apisixoperatorimage.apisixopPrereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.apisixoperatorimage.pullPolicy -}}
  {{- end -}}
{{- end -}}


{{/*
Create KOPF cli option for the comma seperated list of namespaces in monitoredNamespaces:
"<ns1>,<ns1>,...<nsN>"-> "-n <ns1> -n <ns2> ... -n <nsN>" 
*/}}
{{- define "api-operator-apisix.monitoredNamespacesCLIOpts" -}}
{{- printf "-n %s" .Values.deployment.monitoredNamespaces | replace "," " -n " }}
{{- end -}}
