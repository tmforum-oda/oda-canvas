const k8s = require('@kubernetes/client-node');
const assert = require('assert');
const stream = require('stream');
const https = require('https');
const http = require('http');

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const PROMETHEUS_GROUP = "monitoring.coreos.com";
const PROMETHEUS_VERSION = "v1";
const SERVICEMONITOR_PLURAL = "servicemonitors";

const observabilityUtils = {

  /**
   * Function that returns a ServiceMonitor resource
   * @param {String} serviceMonitorName - Name of the ServiceMonitor resource
   * @param {String} namespace - Namespace where the ServiceMonitor should exist
   * @return {Object|null} - The ServiceMonitor resource object, or null if not found
   */
  getServiceMonitor: async function (serviceMonitorName, namespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
      const response = await k8sCustomApi.getNamespacedCustomObject(
        PROMETHEUS_GROUP,
        PROMETHEUS_VERSION,
        namespace,
        SERVICEMONITOR_PLURAL,
        serviceMonitorName
      );
      return response.body;
    } catch (error) {
      if (error.response && error.response.statusCode === 404) {
        return null; // ServiceMonitor not found
      }
      throw error;
    }
  },







  // ==================== OpenTelemetry Functions ====================



  /**
   * Check if OpenTelemetry collector is reachable on specified port
   * @param {Number} port - Port number to check
   * @return {Boolean} - True if collector is reachable
   */
  isCollectorReachable: async function (port = 4318) {
    try {
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      const services = await k8sCoreApi.listNamespacedService('monitoring');
      
      const collectorService = services.body.items.find(service => 
        service.metadata.name.includes('opentelemetry-collector')
      );
      
      if (!collectorService) {
        return false;
      }
      
      return collectorService.spec.ports.some(p => p.port === port);
    } catch (error) {
      console.error(`Error checking collector reachability: ${error.message}`);
      return false;
    }
  },



  // ==================== Helper Functions ====================

  /**
   * Get metrics from the OpenTelemetry Collector
   * @param {Number} metricsPort - Port for the collector metrics endpoint (default: 8888)
   * @return {Object} - Metrics data from the collector
   */
  getCollectorMetrics: async function (metricsPort = 8888) {
    console.log('Getting OpenTelemetry Collector metrics...');
    
    try {
      console.log('Attempting to get metrics via port-forwarded localhost...');
      return await this.getCollectorMetricsViaLocalhost(metricsPort);
    } catch (localhostError) {
      // Provide detailed error message for connection issues
      let errorMessage = `Failed to get collector metrics: ${localhostError.message}`;
      
      if (localhostError.message.includes('Connection failed') || 
          localhostError.message.includes('ECONNREFUSED') ||
          localhostError.message.includes('Request timeout')) {
        
        errorMessage = 'Cannot connect to OpenTelemetry Collector metrics endpoint. ' +
                      'Please ensure port-forwarding is running: ' +
                      'kubectl port-forward -n monitoring deployment/observability-opentelemetry-collector 8888:8888';
      }
      
      throw new Error(errorMessage);
    }
  },


  /**
   * Get metrics from the OpenTelemetry Collector via localhost (port-forwarded)
   * @param {Number} metricsPort - Port for the collector metrics endpoint (default: 8888)
   * @return {Object} - Metrics data from the collector
   */
  getCollectorMetricsViaLocalhost: async function (metricsPort = 8888) {
    return new Promise((resolve, reject) => {
      const url = `http://localhost:${metricsPort}/metrics`;
      console.log(`Attempting to connect to port-forwarded endpoint: ${url}`);
      
      const req = http.get(url, { timeout: 10000 }, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          try {
            if (res.statusCode !== 200) {
              reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
              return;
            }
            
            if (!data || data.trim().length === 0) {
              reject(new Error('No metrics data received from collector'));
              return;
            }
            
            console.log(`Successfully retrieved ${data.length} characters of metrics data`);
            console.log(`First 200 chars: ${data.substring(0, 200)}...`);
            
            // Parse prometheus metrics format
            const metrics = this.parsePrometheusMetrics(data);
            
            if (Object.keys(metrics).length === 0) {
              reject(new Error('No valid metrics found in collector response'));
              return;
            }
            
            console.log(`Parsed ${Object.keys(metrics).length} metrics from collector`);
            resolve(metrics);
          } catch (parseError) {
            reject(new Error(`Failed to parse metrics: ${parseError.message}`));
          }
        });
      });
      
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Request timeout - OpenTelemetry Collector metrics endpoint not responding. Ensure port-forward is running: kubectl port-forward -n monitoring deployment/observability-opentelemetry-collector 8888:8888'));
      });
      
      req.on('error', (error) => {
        reject(new Error(`Connection failed: ${error.message}. Ensure port-forward is running: kubectl port-forward -n monitoring deployment/observability-opentelemetry-collector 8888:8888`));
      });
    });
  },

  /**
   * Parse Prometheus metrics format into key-value pairs
   * @param {String} metricsText - Raw metrics text in Prometheus format
   * @return {Object} - Parsed metrics as key-value pairs
   */
  parsePrometheusMetrics: function (metricsText) {
    const metrics = {};
    
    if (!metricsText) {
      return metrics;
    }
    
    const lines = metricsText.split('\n');
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Skip comments and empty lines
      if (!trimmedLine || trimmedLine.startsWith('#')) {
        continue;
      }
      
      // Parse metric line (format: metric_name{labels} value timestamp)
      const spaceIndex = trimmedLine.lastIndexOf(' ');
      if (spaceIndex === -1) {
        continue;
      }
      
      const metricPart = trimmedLine.substring(0, spaceIndex);
      const valuePart = trimmedLine.substring(spaceIndex + 1);
      
      // Extract metric name (before any labels)
      const labelIndex = metricPart.indexOf('{');
      const metricName = labelIndex === -1 ? metricPart : metricPart.substring(0, labelIndex);
      
      // Parse value (may include timestamp)
      const value = parseFloat(valuePart.split(' ')[0]);
      
      if (!isNaN(value)) {
        // For simplicity, we're storing just the metric name and value
        // In a more complex implementation, you might want to preserve labels
        if (!metrics[metricName]) {
          metrics[metricName] = value;
        } else {
          // If metric already exists (different labels), sum the values
          metrics[metricName] += value;
        }
      }
    }
    
    return metrics;
  },

  /**
   * Get specific OpenTelemetry Collector metrics
   * @return {Object} - Collector-specific metrics
   */
  getCollectorTelemetryMetrics: async function () {
    try {
      const allMetrics = await this.getCollectorMetrics();
      
      // Extract relevant OpenTelemetry Collector metrics
      return {
        // Receiver metrics
        receivedSpans: allMetrics['otelcol_receiver_accepted_spans'] || 0,
        refusedSpans: allMetrics['otelcol_receiver_refused_spans'] || 0,
        receivedMetricPoints: allMetrics['otelcol_receiver_accepted_metric_points'] || 0,
        refusedMetricPoints: allMetrics['otelcol_receiver_refused_metric_points'] || 0,
        receivedLogRecords: allMetrics['otelcol_receiver_accepted_log_records'] || 0,
        refusedLogRecords: allMetrics['otelcol_receiver_refused_log_records'] || 0,
        
        // Exporter metrics
        exportedSpans: allMetrics['otelcol_exporter_sent_spans'] || 0,
        failedSpans: allMetrics['otelcol_exporter_send_failed_spans'] || 0,
        exportedMetricPoints: allMetrics['otelcol_exporter_sent_metric_points'] || 0,
        failedMetricPoints: allMetrics['otelcol_exporter_send_failed_metric_points'] || 0,
        exportedLogRecords: allMetrics['otelcol_exporter_sent_log_records'] || 0,
        failedLogRecords: allMetrics['otelcol_exporter_send_failed_log_records'] || 0,
        
        // Processor metrics
        droppedSpans: allMetrics['otelcol_processor_dropped_spans'] || 0,
        droppedMetricPoints: allMetrics['otelcol_processor_dropped_metric_points'] || 0,
        droppedLogRecords: allMetrics['otelcol_processor_dropped_log_records'] || 0,
        
        // General metrics
        uptime: allMetrics['otelcol_process_uptime'] || 0,
        memoryUsage: allMetrics['otelcol_process_memory_rss'] || 0
      };
    } catch (error) {
      console.error(`Error getting collector telemetry metrics: ${error.message}`);
      throw error;
    }
  },

};

module.exports = observabilityUtils;
