{{- define "canvas-portal.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "canvas-portal.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := include "canvas-portal.name" . -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "canvas-portal.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "canvas-portal.labels" -}}
helm.sh/chart: {{ include "canvas-portal.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "canvas-portal.selectorLabels" -}}
app.kubernetes.io/name: {{ include "canvas-portal.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "canvas-portal.frontend.fullname" -}}
{{- printf "%s-frontend" (include "canvas-portal.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "canvas-portal.backend.fullname" -}}
{{- printf "%s-backend" (include "canvas-portal.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "canvas-portal.backend.pvcName" -}}
{{- default (printf "%s-data" (include "canvas-portal.backend.fullname" .)) .Values.backend.persistence.existingClaim | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "canvas-portal.backend.pvName" -}}
{{- default (printf "%s-data" (include "canvas-portal.backend.fullname" .)) .Values.backend.persistence.persistentVolume.name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "canvas-portal.backend.serviceAccountName" -}}
{{- printf "%s-sa" (include "canvas-portal.backend.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "canvas-portal.frontend.labels" -}}
{{ include "canvas-portal.labels" . }}
app.kubernetes.io/component: frontend
{{- end -}}

{{- define "canvas-portal.backend.labels" -}}
{{ include "canvas-portal.labels" . }}
app.kubernetes.io/component: backend
{{- end -}}

{{- define "canvas-portal.frontend.selectorLabels" -}}
{{ include "canvas-portal.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end -}}

{{- define "canvas-portal.backend.selectorLabels" -}}
{{ include "canvas-portal.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end -}}

{{- define "canvas-portal.keycloak.proxyUpstream" -}}
{{- $url := trimSuffix "/" .Values.frontend.nginx.keycloakUpstream -}}
{{- if and (eq .Values.backend.env.IDM_PROVIDER "keycloak") (not $url) -}}
{{- fail "Keycloak is enabled but frontend.nginx.keycloakUpstream is not configured." -}}
{{- end -}}
{{- default "http://127.0.0.1:65535/auth" $url -}}
{{- end -}}

{{- define "canvas-portal.keycloak.backendUrl" -}}
{{- $url := trimSuffix "/" .Values.backend.env.KEYCLOAK_URL -}}
{{- if and (eq .Values.backend.env.IDM_PROVIDER "keycloak") (not $url) -}}
{{- fail "Keycloak is enabled but backend.env.KEYCLOAK_URL is not configured." -}}
{{- end -}}
{{- $url -}}
{{- end -}}
