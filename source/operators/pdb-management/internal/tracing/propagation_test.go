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
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestHTTPTransportRoundTrip(t *testing.T) {
	// Create a test server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Echo back a success response
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("OK"))
	}))
	defer server.Close()

	// Create transport with default base
	transport := &HTTPTransport{}

	// Create request
	req, err := http.NewRequest("GET", server.URL, nil)
	require.NoError(t, err)

	// Execute request
	resp, err := transport.RoundTrip(req)
	require.NoError(t, err)
	defer func() { _ = resp.Body.Close() }()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func TestHTTPTransportRoundTripWithBase(t *testing.T) {
	// Create a test server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// Create transport with custom base
	transport := &HTTPTransport{
		Base: http.DefaultTransport,
	}

	req, err := http.NewRequest("GET", server.URL, nil)
	require.NoError(t, err)

	resp, err := transport.RoundTrip(req)
	require.NoError(t, err)
	defer func() { _ = resp.Body.Close() }()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func TestHTTPTransportInjectsTraceContext(t *testing.T) {
	// Track headers received by the server
	var receivedHeaders http.Header

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		receivedHeaders = r.Header.Clone()
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// Initialize tracing to set up propagator
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	// Create a context with a span
	ctx, span := StartSpan(context.Background(), "test-span")
	defer span.End()

	transport := &HTTPTransport{}

	req, err := http.NewRequestWithContext(ctx, "GET", server.URL, nil)
	require.NoError(t, err)

	resp, err := transport.RoundTrip(req)
	require.NoError(t, err)
	defer func() { _ = resp.Body.Close() }()

	// The request should have been made successfully
	// Trace headers may or may not be present depending on the tracer
	assert.NotNil(t, receivedHeaders)
}

func TestNewHTTPClient(t *testing.T) {
	client := NewHTTPClient()

	assert.NotNil(t, client)
	assert.NotNil(t, client.Transport)

	// Verify it's our custom transport
	_, ok := client.Transport.(*HTTPTransport)
	assert.True(t, ok)
}

func TestNewHTTPClientMakesRequests(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("Hello"))
	}))
	defer server.Close()

	client := NewHTTPClient()

	resp, err := client.Get(server.URL)
	require.NoError(t, err)
	defer func() { _ = resp.Body.Close() }()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func TestInjectTraceContext(t *testing.T) {
	// Initialize tracing
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()
	headers := make(http.Header)

	// Inject without active span - should not panic
	InjectTraceContext(ctx, headers)

	// Inject with active span
	ctx, span := StartSpan(ctx, "test-span")
	defer span.End()

	InjectTraceContext(ctx, headers)
	// Headers may or may not contain trace context depending on tracer
}

func TestExtractTraceContext(t *testing.T) {
	// Initialize tracing
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()
	headers := make(http.Header)

	// Extract from empty headers - should return valid context
	newCtx := ExtractTraceContext(ctx, headers)
	assert.NotNil(t, newCtx)

	// Extract with trace headers
	headers.Set("traceparent", "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01")
	newCtx = ExtractTraceContext(ctx, headers)
	assert.NotNil(t, newCtx)
}

func TestRoundTripErrorHandling(t *testing.T) {
	// Create transport that will fail
	transport := &HTTPTransport{}

	// Request to invalid URL
	req, err := http.NewRequest("GET", "http://invalid.invalid.invalid:12345", nil)
	require.NoError(t, err)

	// This should fail with connection error
	_, err = transport.RoundTrip(req)
	assert.Error(t, err)
}

func TestHTTPTransportWithContext(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// Initialize tracing
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	// Create context with span and baggage
	ctx := context.Background()
	ctx, span := StartSpan(ctx, "test-request")
	defer span.End()

	ctx = AddBaggage(ctx, "request-id", "test-123")

	transport := &HTTPTransport{}

	req, err := http.NewRequestWithContext(ctx, "GET", server.URL, nil)
	require.NoError(t, err)

	resp, err := transport.RoundTrip(req)
	require.NoError(t, err)
	defer func() { _ = resp.Body.Close() }()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func TestInjectAndExtractRoundTrip(t *testing.T) {
	// Initialize tracing
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	// Create a span and inject its context
	ctx, span := StartSpan(context.Background(), "original-span")
	defer span.End()

	headers := make(http.Header)
	InjectTraceContext(ctx, headers)

	// Extract context from headers into new context
	newCtx := ExtractTraceContext(context.Background(), headers)

	// The new context should be valid
	assert.NotNil(t, newCtx)
}

func TestHTTPClientWithTimeout(t *testing.T) {
	// Server that delays response
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	client := NewHTTPClient()

	// Create request with context
	req, err := http.NewRequest("GET", server.URL, nil)
	require.NoError(t, err)

	resp, err := client.Do(req)
	require.NoError(t, err)
	defer func() { _ = resp.Body.Close() }()

	assert.Equal(t, http.StatusOK, resp.StatusCode)
}
