{{/*
build the full docker image name from image + version + prereleaseSuffix
*/}}
{{- define "secretsmanagementoperator.dockerimage" -}}
  {{- .Values.image -}}:{{- .Values.version -}}
  {{- if .Values.prereleaseSuffix -}}
    -{{- .Values.prereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
build the full sidedcar docker image name from image + version + prereleaseSuffix
*/}}
{{- define "secretsmanagementoperator.sidecarDockerimage" -}}
  {{- .Values.sidecarImage -}}:{{- .Values.sidecarVersion -}}
  {{- if .Values.sidecarPrereleaseSuffix -}}
    -{{- .Values.sidecarPrereleaseSuffix -}}
  {{- end -}}
{{- end -}}
