{{/*
Expand the name of the chart.
*/}}
{{- define "credentialsmanagement-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "credentialsmanagement-operator.fullname" -}}
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
{{- define "credentialsmanagement-operator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "credentialsmanagement-operator.labels" -}}
helm.sh/chart: {{ include "credentialsmanagement-operator.chart" . }}
{{ include "credentialsmanagement-operator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "credentialsmanagement-operator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "credentialsmanagement-operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "credentialsmanagement-operator.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "credentialsmanagement-operator.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
build the full credop docker image name from image + version + prereleaseSuffix
*/}}
{{- define "credentialsmanagement-operator.credopImage" -}}
  {{- .Values.deployment.credopImage -}}:{{- .Values.deployment.credopVersion -}}
  {{- if .Values.deployment.credopPrereleaseSuffix -}}
    -{{- .Values.deployment.credopPrereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
overwrite credop imagePullSecret with "Always" if prereleaseSuffix is set
*/}}
{{- define "credentialsmanagement-operator.imagePullPolicy" -}}
  {{- if .Values.deployment.credopPrereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.deployment.imagePullPolicy -}}
  {{- end -}}
{{- end -}}