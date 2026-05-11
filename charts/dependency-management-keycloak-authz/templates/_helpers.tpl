{{/*
Expand the name of the chart.
*/}}
{{- define "dependency-management-keycloak-authz.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "dependency-management-keycloak-authz.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
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
{{- define "dependency-management-keycloak-authz.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "dependency-management-keycloak-authz.labels" -}}
helm.sh/chart: {{ include "dependency-management-keycloak-authz.chart" . }}
{{ include "dependency-management-keycloak-authz.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "dependency-management-keycloak-authz.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dependency-management-keycloak-authz.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Build the full operator docker image name, appending prereleaseSuffix when set.
*/}}
{{- define "dependency-management-keycloak-authz.image" -}}
  {{ include "docker.registry" . }}{{- .Values.deployment.image -}}:{{- .Values.deployment.version -}}
  {{- if .Values.deployment.prereleaseSuffix -}}
    -{{- .Values.deployment.prereleaseSuffix -}}
  {{- end -}}
{{- end -}}

{{/*
Use imagePullPolicy "Always" when a prereleaseSuffix is set, to ensure the
latest pre-release image is always pulled. Otherwise use the configured policy.
*/}}
{{- define "dependency-management-keycloak-authz.imagePullPolicy" -}}
  {{- if .Values.deployment.prereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.deployment.imagePullPolicy -}}
  {{- end -}}
{{- end -}}

{{/*
Image pull secrets block, indented for use inside a pod spec.
*/}}
{{- define "image-pull-secrets" -}}
{{- range .Values.global.imagePullSecrets }}
- name: {{ . }}
{{- end }}
{{- end }}

{{/*
Fallback docker.registry helper — returns empty string when not defined by a
parent chart, so plain image names are used as-is.
*/}}
{{- define "docker.registry" -}}
{{- "" -}}
{{- end -}}
