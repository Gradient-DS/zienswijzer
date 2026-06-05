{{/*
Expand the name of the chart.
*/}}
{{- define "zienswijzer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a fully qualified app name.
*/}}
{{- define "zienswijzer.fullname" -}}
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
Chart name and version label.
*/}}
{{- define "zienswijzer.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "zienswijzer.labels" -}}
helm.sh/chart: {{ include "zienswijzer.chart" . }}
{{ include "zienswijzer.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels (release-wide).
*/}}
{{- define "zienswijzer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "zienswijzer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Per-component selector labels. Call with (dict "ctx" . "component" "api").
*/}}
{{- define "zienswijzer.componentSelectorLabels" -}}
{{ include "zienswijzer.selectorLabels" .ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Per-component full labels. Call with (dict "ctx" . "component" "api").
*/}}
{{- define "zienswijzer.componentLabels" -}}
{{ include "zienswijzer.labels" .ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end }}
