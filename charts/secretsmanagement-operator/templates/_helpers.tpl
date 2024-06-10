{{/*
build the full docker image name from image + version + prereleaseSuffix
*/}}
{{- define "secretsmanagementoperator.dockerimage" -}}
{{- .Values.image -}}:{{- .Values.version -}}
{{- if .Values.prereleaseSuffix -}}-{{- .Values.prereleaseSuffix -}}{{- end -}}
{{- end -}}

