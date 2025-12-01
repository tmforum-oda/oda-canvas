/*
Copyright 2025.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package tracing

import (
	"context"
	"net/http"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
)

// HTTPTransport wraps an http.RoundTripper with trace propagation
type HTTPTransport struct {
	Base http.RoundTripper
}

// RoundTrip implements http.RoundTripper with trace context propagation
func (t *HTTPTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	// Inject trace context into outgoing request
	otel.GetTextMapPropagator().Inject(req.Context(), propagation.HeaderCarrier(req.Header))

	// Use base transport or default
	base := t.Base
	if base == nil {
		base = http.DefaultTransport
	}

	return base.RoundTrip(req)
}

// NewHTTPClient creates an HTTP client with trace propagation
func NewHTTPClient() *http.Client {
	return &http.Client{
		Transport: &HTTPTransport{
			Base: http.DefaultTransport,
		},
	}
}

// InjectTraceContext injects trace context into headers for manual propagation
func InjectTraceContext(ctx context.Context, headers http.Header) {
	otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(headers))
}

// ExtractTraceContext extracts trace context from incoming headers
func ExtractTraceContext(ctx context.Context, headers http.Header) context.Context {
	return otel.GetTextMapPropagator().Extract(ctx, propagation.HeaderCarrier(headers))
}
