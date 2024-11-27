{{/*
Expand the name of the chart.
*/}}
{{- define "component-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "component-operator.fullname" -}}
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
{{- define "component-operator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "component-operator.labels" -}}
helm.sh/chart: {{ include "component-operator.chart" . }}
{{ include "component-operator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "component-operator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "component-operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "component-operator.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "component-operator.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
build the full compop docker image name from image + version + prereleaseSuffix
*/}}
{{- define "component-operator.compopDockerimage" -}}
  {{- .Values.deployment.compopImage -}}:{{- .Values.deployment.compopVersion -}}
  {{- if .Values.deployment.compopPrereleaseSuffix -}}
    -{{- .Values.deployment.compopPrereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
build the full idconfop docker image name from image + version + prereleaseSuffix
*/}}
{{- define "component-operator.idconfopDockerimage" -}}
  {{- .Values.deployment.idconfopImage -}}:{{- .Values.deployment.idconfopVersion -}}
  {{- if .Values.deployment.idconfopPrereleaseSuffix -}}
    -{{- .Values.deployment.idconfopPrereleaseSuffix -}}
  {{- end -}}
{{- end -}}


{{/*
overwrite compop imagePullSecret with "Always" if prereleaseSuffix is set
*/}}
{{- define "component-operator.compopImagePullPolicy" -}}
  {{- if .Values.deployment.compopPrereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.deployment.compopImagePullPolicy -}}
  {{- end -}}
{{- end -}}


{{/*
overwrite idconfop imagePullSecret with "Always" if prereleaseSuffix is set
*/}}
{{- define "component-operator.idconfopImagePullPolicy" -}}
  {{- if .Values.deployment.idconfopPrereleaseSuffix -}}
    Always
  {{- else -}}
    {{- .Values.deployment.idconfopImagePullPolicy -}}
  {{- end -}}
{{- end -}}
