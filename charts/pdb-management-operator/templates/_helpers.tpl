{{- define "pdb-management-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "pdb-management-operator.fullname" -}}
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

{{- define "pdb-management-operator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "pdb-management-operator.labels" -}}
helm.sh/chart: {{ include "pdb-management-operator.chart" . }}
{{ include "pdb-management-operator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "pdb-management-operator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pdb-management-operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "pdb-management-operator.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "pdb-management-operator.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "pdb-management-operator.dockerImage" -}}
{{- .Values.deployment.image -}}:{{- .Values.deployment.version -}}
{{- if .Values.deployment.prereleaseSuffix -}}
-{{- .Values.deployment.prereleaseSuffix -}}
{{- end -}}
{{- end -}}

{{- define "pdb-management-operator.imagePullPolicy" -}}
{{- if .Values.deployment.prereleaseSuffix -}}
Always
{{- else -}}
{{- .Values.deployment.imagePullPolicy -}}
{{- end -}}
{{- end -}}

