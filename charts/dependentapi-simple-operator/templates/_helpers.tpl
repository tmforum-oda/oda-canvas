
{{/*
build the full seccon docker image name from image + version + prereleaseSuffix
*/}}
{{- define "dependentapi-simple-operator.dockerimage" -}}
  {{- .Values.image -}}:{{- .Values.version -}}
  {{- if .Values.prereleaseSuffix -}}
    -{{- .Values.prereleaseSuffix -}}
  {{- end -}}
{{- end -}}


