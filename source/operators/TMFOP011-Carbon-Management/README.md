# TMFOP011 Carbon Management Operators

Enables carbon-aware computing by measuring energy and carbon consumption of ODA Components and providing services to optimize workload operations based on carbon intensity data. This operator reduces the environmental impact of software by dynamically adjusting resource allocation during periods of high-carbon electricity generation.

[![Carbon Aware Software - Optimizing Telecom Workloads for a Greener Grid](https://img.youtube.com/vi/I78MSow6RQg/0.jpg)](https://youtu.be/I78MSow6RQg)

---

At present, there is one implementation:

* [Carbon Management Operator](./carbon-management/): Kubernetes operator that integrates with KEDA to provide carbon-aware autoscaling based on real-time carbon intensity data from TMF628 Performance Management API.

## Overview

The Carbon Management Operator enables ODA Components to minimize their carbon footprint by automatically adjusting workload scaling based on real-time carbon intensity data from electrical grids. This approach allows organizations to reduce environmental impact without requiring application code changes, by scaling down during periods when the electrical grid relies more heavily on fossil fuels and scaling up when renewable energy sources are more prevalent.

## Key Concepts

### Carbon Intensity

Carbon intensity measures the amount of carbon dioxide equivalent (CO2e) emitted per kilowatt-hour (kWh) of electricity consumed. It is typically expressed in grams of CO2e per kWh (gCO2eq/kWh) and quantifies the carbon emissions associated with energy usage. Carbon intensity varies based on:

- **Time of day**: Renewable energy availability fluctuates (solar during day, wind varies)
- **Geographic location**: Energy mix differs by region (some regions have more renewables)
- **Grid conditions**: Peak demand may require fossil fuel generation

### Carbon Awareness

Carbon awareness refers to understanding that the environmental impact of electricity consumption varies based on the time and location of use. This variation is due to the fluctuating availability of renewable energy sources. Electricity is generated from a mix of sources, each with its own carbon emissions profile:

- **Renewable sources** (wind, solar, hydro): Minimal carbon emissions
- **Fossil fuels** (natural gas, coal): Significantly more carbon-intensive
- **Energy mix impact**: The carbon footprint is determined by both the source and the amount consumed

### Carbon-Aware Software

Carbon-aware software is designed to optimize electricity usage by:

- **Increasing consumption** during periods when the grid is powered by cleaner, low-carbon sources
- **Reducing consumption** when the grid relies more on high-carbon sources
- **Making intelligent decisions** based on real-time carbon intensity data

[Studies](https://ieeexplore.ieee.org/document/6128960) indicate that carbon-aware practices can achieve carbon reductions ranging from 45% to 99%, depending on the proportion of renewables in the energy mix.

## Strategies for Carbon Awareness in Software

### 1. Scheduling Workloads Based on Carbon Intensity

Workload scheduling can be achieved without modifying the workloads themselves by developing a Kubernetes operator that leverages the Kubernetes Scheduler. This operator allocates workloads based on the carbon intensity of electrical grids, independent of workload usage patterns.

**How it works**:
1. Kubernetes Scheduler ensures Pods are evenly distributed across Nodes while maintaining sufficient resources (memory, CPU)
2. Carbon intensity data is retrieved from third-party providers ([WattTime](https://watttime.org/), [Electricity Maps](https://www.electricitymaps.com/))
3. Operator queries APIs to retrieve carbon intensity data for the location of each Node
4. Operator generates configuration containing this information
5. Configuration is injected into the Kubernetes Scheduler, enabling it to assign Nodes to Pods based on carbon intensity
6. Configuration is periodically updated and re-applied as carbon intensity fluctuates

**Considerations**: To implement effectively without disrupting business requirements, factors such as infrastructure complexity, latency, and data sovereignty must be considered.

**Resources**:
- Green Software Foundation: [Carbon-Aware Kubernetes](https://greensoftware.foundation/articles/Carbon-Aware-kubernetes)
- Research paper: [A Low Carbon Kubernetes Scheduler](http://ceur-ws.org/Vol-2382/ICT4S2019_paper_28.pdf)
- Study: [Carbon emission-aware job scheduling for Kubernetes deployments](https://link.springer.com/article/10.1007/s11227-023-05506-7)

**Status**: *Implementation Planned*

### 2. Scaling Workloads Based on Carbon Intensity

Workloads can be scaled without modifying their code by creating a Kubernetes operator that integrates with KEDA (Kubernetes Event-Driven Autoscaler). This operator uses carbon intensity data to guide scaling decisions independently of workload usage patterns.

**How it works**:
1. Operator queries carbon intensity APIs to retrieve location-specific data
2. Operator creates and manages KEDA `ScaledObject` resources for each deployment
3. `maxReplicaCount` is dynamically adjusted based on carbon intensity thresholds:
   - During low carbon intensity → Allow higher replica counts
   - During high carbon intensity → Restrict replica counts
4. KEDA continues to scale based on workload metrics (CPU, memory, custom metrics) but within the carbon-adjusted limits
5. Configuration is regularly updated as carbon intensity fluctuates

**Benefits**:
- No application code changes required
- Declarative configuration through Kubernetes custom resources
- Automatic discovery and management of deployments
- Works alongside existing KEDA triggers (Prometheus, CPU, memory, etc.)

**Inspiration**: [Azure Carbon-Aware KEDA Operator](https://github.com/Azure/carbon-aware-keda-operator)

**Status**: *Implemented* - See [carbon-management/](./carbon-management/)

## Use Cases for Carbon-Aware Software

Carbon-aware software is most effective for workloads that are:
- **Time-flexible**: Not requiring immediate execution
- **Interruptible**: Can tolerate scaling adjustments
- **Non-critical**: Development, test, or batch processing environments

### Suitable Workloads

- **Machine Learning (ML) training jobs**: Compute-intensive and not time-sensitive. Scheduling ML training during times of lower carbon intensity can reduce emissions by up to 15%, while relocating training to greener regions can achieve reductions of 50% or more.
- **Non-critical data backups**: Can be scheduled during low-carbon periods
- **Batch processing jobs**: Periodic data processing that tolerates delays
- **Data analytics tasks**: Large-scale analysis that doesn't require real-time results
- **CI/CD pipelines**: Development and testing workloads in non-production environments
- **Software updates and deployments**: Can be scheduled during greener energy windows

### Benefits

Leveraging carbon intensity data to optimize workload execution helps organizations:

- **Reduce emissions**: Achieve measurable carbon footprint reduction
- **Identify opportunities**: Use data to run hypothetical models and find optimization opportunities
- **Build business cases**: Demonstrate environmental and cost benefits
- **Contribute to sustainability**: Support renewable energy adoption and grid stability
