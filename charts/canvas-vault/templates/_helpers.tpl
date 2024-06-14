{{/*
Allow the release namespace to be overridden
*/}}
{{- define "canvasvault.namespace" -}}
{{- default .Release.Namespace .Values.vault.global.namespace -}}
{{- end -}}

