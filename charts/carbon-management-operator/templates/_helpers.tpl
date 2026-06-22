{{/*
Expand the name of the chart.
*/}}
{{- define "carbon-management-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "carbon-management-operator.fullname" -}}
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
{{- define "carbon-management-operator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "carbon-management-operator.labels" -}}
helm.sh/chart: {{ include "carbon-management-operator.chart" . }}
{{ include "carbon-management-operator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "carbon-management-operator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "carbon-management-operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "carbon-management-operator.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "carbon-management-operator.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Build the full docker image name from image + version + prereleaseSuffix
*/}}
{{- define "carbon-management-operator.image" -}}
{{ .Values.deployment.image }}:{{ .Values.deployment.version -}}
{{- if .Values.deployment.prereleaseSuffix }}-{{ .Values.deployment.prereleaseSuffix }}{{- end -}}
{{- end }}

{{/*
Override imagePullPolicy with "Always" if prereleaseSuffix is set
*/}}
{{- define "carbon-management-operator.imagePullPolicy" -}}
{{- if .Values.deployment.prereleaseSuffix }}Always{{ else }}{{ .Values.deployment.imagePullPolicy }}{{ end -}}
{{- end }}
