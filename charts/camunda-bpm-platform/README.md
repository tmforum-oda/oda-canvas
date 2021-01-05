<!-- omit in toc -->
# Camunda BPM Platform Helm Chart

A Helm chart for Camunda BPM, the open-source BPM platform.

<!-- omit in toc -->
## ToC
- [Install](#install)
- [Links](#links)
- [Configuration](#configuration)
  - [Image](#image)
  - [Database](#database)
  - [Metrics](#metrics)
  - [Misc](#misc)

## Install

```sh
$ helm repo add camunda https://helm.camunda.cloud
$ helm repo update
$ helm install demo camunda/camunda-bpm-platform
```

## Links

* Camunda homepage: https://camunda.com
* Camunda BPM Platform repo: https://github.com/camunda/camunda-bpm-platform
* Camunda BPM Platform Docker image: https://github.com/camunda/docker-camunda-bpm-platform

## Configuration

### Image

Camunda BPM open-source Docker image comes in 3 distributions `tomcat`, `wildfly`, and `run`.
Each distro has different tags, check the list of [supported tags/releases](https://github.com/camunda/docker-camunda-bpm-platform#supported-tagsreleases) by the docker project for more details.

The image used in the chart is `tomcat-latest`.

### Database

Camunda BPM has 2 options in terms of databases.

<!-- omit in toc -->
#### Internal database
The H2 database is used by default which works fine if you just want to test Camunda BPM Platform.
But since the database is embedded, only 1 deployment replica could be used.

<!-- omit in toc -->
#### External database
Databases like PostgreSQL or MySQL could be used also which is the same as in production.
Here is an example to use PostgreSQL as an external database.

First, create the secret that has the database credentials.

```sh
$ kubectl create secret generic                 \
    camunda-bpm-platform-postgresql-credentials \
    --from-literal=DB_USERNAME=foo              \
    --from-literal=DB_PASSWORD=bar
```

Then set the values to use the external database:

```yaml
database:
  internal:
    enabled: false
  external:
    enabled: true
    credentialsSecertName: camunda-bpm-platform-postgresql-credentials
    driver: "org.postgresql.Driver"
    url: "jdbc:postgresql://cambpm-demo-db:5432/process-engine"
```

**Please note**, this Helm chart doesn't manage any external database, it just uses what's configured.

### Metrics

To get Prometheus metrics for Camunda BPM, it could be enabled in values file using:

```yaml
metrics:
  enabled: true
```

If there is Prometheus is setup it will scrap the metrics service automatically.

### Misc

* Debugging in the Camunda BPM container could be enabled by setting `general.debug: true`.