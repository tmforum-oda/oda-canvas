{{/*
Custom/private docker image registry
*/}}
{{- define "docker.registry" -}}
{{- if .Values.global }}
{{- if .Values.global.image }}
{{- if .Values.global.image.registry }}
{{- $registry := (trimSuffix "/" .Values.global.image.registry) }}
{{- printf "%s/" $registry }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create image pull secrets
*/}}
{{- define "image-pull-secrets" -}}
{{- if .Values.global }}
{{- if .Values.global.imagePullSecrets }}
{{- range .Values.global.imagePullSecrets }}
  {{- if eq (typeOf .) "map[string]interface {}" }}
- {{ toYaml . | nindent 0 | trim }}
  {{- else }}
- name: {{ . }}
  {{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Expand the name of the chart.
*/}}
{{- define "component-registry.name" -}}
{{- default "compreg" .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "component-registry.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default "compreg" .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "component-registry.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "component-registry.labels" -}}
helm.sh/chart: {{ include "component-registry.chart" . }}
{{ include "component-registry.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: oda-canvas
{{- end }}

{{/*
Selector labels
*/}}
{{- define "component-registry.selectorLabels" -}}
app.kubernetes.io/name: {{ include "component-registry.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "component-registry.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "component-registry.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
External name, defaults to release name if not explicitly set
*/}}
{{- define "component-registry.externalName" -}}
{{- default .Release.Name .Values.externalName }}
{{- end }}


{{/*
build the full component registry docker image name from image + version + prereleaseSuffix
*/}}
{{- define "component-registry.dockerimage" -}}
  {{ include "docker.registry" .}}{{- .Values.image -}}:{{- .Values.version -}}
  {{- if .Values.prereleaseSuffix -}}
    -{{- .Values.prereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
overwrite imagePullSecret with "Always" if prereleaseSuffix is set
*/}}
{{- define "component-registry.imagePullPolicy" -}}
  {{- if .Values.prereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.imagePullPolicy -}}
  {{- end -}}
{{- end -}}


{{/*
Return the own registry URL, either from values or constructed from fullname and domain
*/}}
{{- define "component-registry.own-registry-url" -}}
  {{- if .Values.ownRegistryURL -}}
    {{ .Values.ownRegistryURL }}
  {{- else if .Values.domain -}}
    https://{{ include "component-registry.fullname" . }}.{{ .Values.domain }}
  {{- else -}}
    http://{{ include "component-registry.fullname" . }}.canvas.svc.cluster.local
  {{- end -}}
{{- end }}


{{/*
Return the own component registry name, either from values or from release name
*/}}
{{- define "component-registry.own-registry-name" -}}
  {{- if .Values.ownRegistryName -}}
    {{ .Values.ownRegistryName }}
  {{- else -}}
    {{ .Release.Name }}
  {{- end -}}
{{- end }}


