{{/*
build the full oauth2 envoyfilter operator docker image name from image + version + prereleaseSuffix
*/}}
{{- define "oauth2-envoyfilter-operator.dockerimage" -}}
  {{- .Values.image -}}:{{- .Values.version -}}
  {{- if .Values.prereleaseSuffix -}}
    -{{- .Values.prereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
overwrite imagePullSecret with "Always" if prereleaseSuffix is set
*/}}
{{- define "oauth2-envoyfilter-operator.imagePullPolicy" -}}
  {{- if .Values.prereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.imagePullPolicy -}}
  {{- end -}}
{{- end -}}


