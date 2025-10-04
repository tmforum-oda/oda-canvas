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
	"fmt"
	"os"
	"strconv"

	"go.opentelemetry.io/otel/baggage"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/exporters/jaeger"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.34.0"
	"go.opentelemetry.io/otel/trace"
	"go.opentelemetry.io/otel/trace/noop"
)

var tracer trace.Tracer

func init() {
	// Initialize with a no-op tracer to prevent nil pointer dereference
	tracer = noop.NewTracerProvider().Tracer("pdb-management")
}

// InitTracing initializes OpenTelemetry tracing
func InitTracing(ctx context.Context, serviceName string) (func(), error) {
	var exporter sdktrace.SpanExporter
	var err error

	// Determine which exporter to use based on environment
	if jaegerEndpoint := os.Getenv("JAEGER_ENDPOINT"); jaegerEndpoint != "" {
		// Use Jaeger exporter
		exporter, err = jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(jaegerEndpoint)))
		if err != nil {
			return nil, fmt.Errorf("failed to create Jaeger exporter: %w", err)
		}
	} else if otlpEndpoint := os.Getenv("OTLP_ENDPOINT"); otlpEndpoint != "" {
		// Use OTLP exporter
		client := otlptracegrpc.NewClient(
			otlptracegrpc.WithEndpoint(otlpEndpoint),
			otlptracegrpc.WithInsecure(),
		)
		exporter, err = otlptrace.New(ctx, client)
		if err != nil {
			return nil, fmt.Errorf("failed to create OTLP exporter: %w", err)
		}
	} else {
		// No endpoint configured - use noop tracer
		tracer = noop.NewTracerProvider().Tracer(serviceName)
		return func() {}, nil
	}

	// Create resource
	res, err := resource.Merge(
		resource.Default(),
		resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceNameKey.String(serviceName),
			semconv.ServiceVersionKey.String(getVersion()),
			attribute.String("operator.type", "pdb-management"),
			attribute.String("kubernetes.namespace", os.Getenv("POD_NAMESPACE")),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}

	// Create tracer provider
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
		sdktrace.WithSampler(sdktrace.TraceIDRatioBased(getSampleRate())),
	)

	// Set global tracer provider
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.TraceContext{})

	// Get tracer
	tracer = tp.Tracer(serviceName)

	// Return cleanup function
	cleanup := func() {
		if err := tp.Shutdown(ctx); err != nil {
			fmt.Printf("Error shutting down tracer provider: %v\n", err)
		}
	}

	return cleanup, nil
}

// StartSpan starts a new span with common attributes
func StartSpan(ctx context.Context, name string, opts ...trace.SpanStartOption) (context.Context, trace.Span) {
	if tracer == nil {
		// Fallback to noop tracer if not initialized
		tracer = noop.NewTracerProvider().Tracer("pdb-management")
	}
	return tracer.Start(ctx, name, opts...)
}

// ReconcileSpan starts a span specifically for reconciliation
func ReconcileSpan(ctx context.Context, controller, namespace, name string) (context.Context, trace.Span) {
	if tracer == nil {
		// Fallback to noop tracer if not initialized
		tracer = noop.NewTracerProvider().Tracer("pdb-management")
	}

	ctx, span := tracer.Start(ctx, fmt.Sprintf("%s.Reconcile", controller),
		trace.WithAttributes(
			attribute.String("controller", controller),
			attribute.String("namespace", namespace),
			attribute.String("name", name),
			attribute.String("operation", "reconcile"),
		),
	)
	return ctx, span
}

// RecordError records an error on the span
func RecordError(span trace.Span, err error, description string) {
	if err != nil && span != nil && span.IsRecording() {
		span.RecordError(err,
			trace.WithAttributes(
				attribute.String("error.description", description),
			),
		)
		span.SetStatus(codes.Error, description)
	}
}

// AddEvent adds an event to the current span
func AddEvent(ctx context.Context, name string, attrs ...attribute.KeyValue) {
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.AddEvent(name, trace.WithAttributes(attrs...))
	}
}

func getSampleRate() float64 {
	if rate := os.Getenv("TRACE_SAMPLE_RATE"); rate != "" {
		if f, err := strconv.ParseFloat(rate, 64); err == nil {
			return f
		}
	}
	return 0.1 // Default 10% sampling
}

func getVersion() string {
	if v := os.Getenv("OPERATOR_VERSION"); v != "" {
		return v
	}
	return "unknown"
}

// CreateLinkedSpan creates a new span linked to an existing span
func CreateLinkedSpan(ctx context.Context, name string, linkedSpanContext trace.SpanContext) (context.Context, trace.Span) {
	if tracer == nil {
		tracer = noop.NewTracerProvider().Tracer("pdb-management")
	}

	link := trace.Link{
		SpanContext: linkedSpanContext,
		Attributes: []attribute.KeyValue{
			attribute.String("link.type", "related_operation"),
		},
	}

	return tracer.Start(ctx, name, trace.WithLinks(link))
}

// ReconcileSpanWithParent starts a span with explicit parent context
func ReconcileSpanWithParent(ctx context.Context, controller, namespace, name string, parentSpanContext trace.SpanContext) (context.Context, trace.Span) {
	if tracer == nil {
		tracer = noop.NewTracerProvider().Tracer("pdb-management")
	}

	// Create span with parent
	ctx = trace.ContextWithSpanContext(ctx, parentSpanContext)

	ctx, span := tracer.Start(ctx, fmt.Sprintf("%s.Reconcile", controller),
		trace.WithAttributes(
			attribute.String("controller", controller),
			attribute.String("namespace", namespace),
			attribute.String("name", name),
			attribute.String("operation", "reconcile"),
		),
	)
	return ctx, span
}

// GetSpanContext returns the current span context
func GetSpanContext(ctx context.Context) trace.SpanContext {
	span := trace.SpanFromContext(ctx)
	if span != nil {
		return span.SpanContext()
	}
	return trace.SpanContext{}
}

// StartSpanWithKind starts a new span with a specific kind
func StartSpanWithKind(ctx context.Context, name string, kind trace.SpanKind, opts ...trace.SpanStartOption) (context.Context, trace.Span) {
	if tracer == nil {
		tracer = noop.NewTracerProvider().Tracer("pdb-management")
	}

	allOpts := append([]trace.SpanStartOption{trace.WithSpanKind(kind)}, opts...)
	return tracer.Start(ctx, name, allOpts...)
}

// AddBaggage adds baggage to the context for propagation
func AddBaggage(ctx context.Context, key, value string) context.Context {
	member, err := baggage.NewMember(key, value)
	if err != nil {
		// If we can't create the member, return the original context
		return ctx
	}
	b, _ := baggage.New(member)
	return baggage.ContextWithBaggage(ctx, b)
}
