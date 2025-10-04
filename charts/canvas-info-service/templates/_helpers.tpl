{{/*
build the full dependent api docker image name from image + version + prereleaseSuffix
*/}}
{{- define "canvas-info-service.dockerimage" -}}
  {{ include "docker.registry" .}}{{- .Values.image -}}:{{- .Values.version -}}
  {{- if .Values.prereleaseSuffix -}}
    -{{- .Values.prereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
overwrite imagePullSecret with "Always" if prereleaseSuffix is set
*/}}
{{- define "canvas-info-service.imagePullPolicy" -}}
  {{- if .Values.prereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.imagePullPolicy -}}
  {{- end -}}
{{- end -}}
