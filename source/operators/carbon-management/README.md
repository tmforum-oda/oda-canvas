# Carbon Management Operator

## Overview
The Carbon Management Operator is designed to optimize energy consumption and reduce carbon emissions by leveraging carbon intensity data. This document outlines the key concepts, strategies, and use cases for implementing carbon-aware software solutions.


## Key Concepts

### Carbon Intensity
Carbon intensity measures the amount of carbon dioxide equivalent (CO2e) emitted per kilowatt-hour (kWh) of electricity consumed. It is typically expressed in grams of CO2e per kWh (gCO2eq/kWh) and quantifies the carbon emissions associated with energy usage.

### Carbon Awareness
Carbon awareness refers to understanding that the environmental impact of electricity consumption varies based on the time and location of use. This variation is due to the fluctuating availability of renewable energy sources. Electricity is generated from a mix of sources, each with its own carbon emissions profile. Renewable sources like wind, solar, and hydro produce minimal carbon emissions, while fossil fuels such as coal and gas are significantly more carbon-intensive, with coal being the highest. The carbon footprint of energy consumption is primarily determined by its source and the amount consumed.

### Carbon-Aware Software
Carbon-aware software is designed to optimize electricity usage by increasing consumption during periods when the grid is powered by cleaner, low-carbon sources and reducing it when the grid relies more on high-carbon sources in order to reduce carbon emissions.

[Studies](https://ieeexplore.ieee.org/document/6128960) indicate that such practices can achieve carbon reductions ranging from 45% to 99%, depending on the proportion of renewables in the energy mix.


## Strategies for Carbon Awareness in Software

### Scheduling Workloads Based on Carbon Intensity
Workload scheduling can be achieved without modifying the workloads themselves by developing a Kubernetes operator that leverages the Kubernetes Scheduler. This operator allocates workloads based on the carbon intensity of electrical grids, independent of workload usage. The Kubernetes Scheduler ensures that Pods are evenly distributed across Nodes while maintaining sufficient resources (e.g., memory, CPU) for workload execution. Carbon intensity data for electrical grids can be sourced from third-party providers such as [WattTime](https://watttime.org/), [Electricity Maps](https://www.electricitymaps.com/), or similar services.

The operator queries APIs to retrieve carbon intensity data for the location of each Node and generates a YAML file containing this information. This YAML file is injected into the Kubernetes Scheduler, enabling it to assign Nodes to Pods based on carbon intensity data, thereby minimizing carbon emissions. Since carbon intensity fluctuates over time, the YAML file should be periodically updated and re-applied to the Scheduler.

To implement this approach effectively without disrupting business requirements, factors such as infrastructure complexity, latency, and data sovereignty must be considered.

For more details, refer to the Green Software Foundation article on [Carbon-Aware Kubernetes](https://greensoftware.foundation/articles/Carbon-Aware-kubernetes). Key algorithms supporting this method are described in the research paper [A Low Carbon Kubernetes Scheduler](http://ceur-ws.org/Vol-2382/ICT4S2019_paper_28.pdf) and in studies on [Carbon emission-aware job scheduling for Kubernetes deployments](https://link.springer.com/article/10.1007/s11227-023-05506-7). Much of the core functionality relies on the Kubernetes Scheduler itself.

### Scaling Workloads Based on Carbon Intensity
Workloads can be scaled without modifying their code by creating a Kubernetes operator that integrates with a KEDA (Kubernetes Event-Driven Autoscaler) scaler. This operator uses carbon intensity data from third-party providers like [WattTime](https://watttime.org/) or [Electricity Maps](https://www.electricitymaps.com/) to guide scaling decisions independently of workload usage. The operator queries these APIs to retrieve location-specific carbon intensity data and stores it in a configMap. This configMap dynamically adjusts the KEDA scaler’s behavior, setting the maxReplicaCount to restrict scaling during periods of high carbon intensity and allowing greater scaling when carbon intensity is low. Since carbon intensity fluctuates over time, the configMap should be regularly updated and re-applied to ensure effective scaling.

A detailed solution for this approach can be found at: [Azure Carbon-Aware KEDA Operator](https://github.com/Azure/carbon-aware-keda-operator).


## Use Cases for Carbon-Aware Software

By utilizing real-time grid carbon intensity data, carbon-aware software can schedule or scale low-priority and time-flexible workloads that support interruptions in dev/test environments, minimizing the overall carbon footprint.

### Examples:
- **Machine Learning (ML) training jobs**: These are typically compute-intensive and not time-sensitive. Scheduling ML training during times of lower carbon intensity can reduce emissions by up to 15%, while relocating training to greener regions can achieve reductions of 50% or more.
- **Other Suitable Candidates**:
  - Non-critical data backups
  - Batch processing jobs
  - Data analytics tasks
  - Building AI models during periods of lower carbon emissions
  - Deploying software to cloud regions with cleaner energy
  - Running software updates during greener energy windows
  - Optimize when and where computational tasks are executed and adjust performance settings.

### Additional Benefits
Leveraging data to run hypothetical models can help organizations:
- Identify opportunities to reduce emissions.
- Build business cases for change.
- Contribute to a more sustainable future.