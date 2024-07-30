# Developer How-Tos: Work with Dockerimages

The project oda-canvas is configured to automatically build docker images, when their source code is changed.
To successfully collaborate in the same repository some rules have to be followed.

## Global Rules

* Release versions (image tags) follow the semantic versioning format "<major>.<minor>.increment>" and are built only from the master branch
* Release versions are immutable and can not be overwritten 
* Prerelease versions have the format "<major>.<minor>.<increment>-<prerelease-suffix>" and are built from feature branches
* Feature branches have the format "feature/*" or "odaa-*"
* Release versions are overwritten every time the source code changed
* The prerelease suffix should be unique for each feature branch, otherwise the same image will be built from different branches and the last build wins
* Versions are stored in the charts/canvas-oda/values.yaml file which is also used for deploying the canvas-oda chart (single source of truth)

## Versions in values.yaml

Dockerimages are versioned in the [values.yaml](charts/canvas-oda/values.yaml) file of the canva-oda chart. 
E.g. for oda-webhook:

```
...
oda-webhook:
  image: tmforumodacanvas/compcrdwebhook
  version: 0.6.3
  prereleaseSuffix: issue123
```

The full dockerimage is set together to "tmforumodacanvas/compcrdwebhook:0.6.3-issue123".

If there is no prereleaseSuffix, the seperator "-" is ommitted: 

```
...
oda-webhook:
  image: tmforumodacanvas/compcrdwebhook
  version: 0.6.2
  prereleaseSuffix:
```

The full docker image is "tmforumodacanvas/compcrdwebhook:0.6.2"

The advantage of using the values.yaml as source for the dockerimage names is,
that when deploying the canvas-oda chart from the filesystem all docker images are automatically build:

A prerelease version is semantically smaller than the release version:

```
0.6.2 < 0.6.3-issue-123 < 0.6.3
```


## Example change code in Secretsmanagement-Operator

To cover the development lifecycle with Dockerimages an example change will be described.

### Create a feature branch 

To do your code changes a feature branch is needed.
Feature branches have to follow the naming convention "feature/..." or "odaa-...".
Let´s assume we are working on the GitHub issue 3456, 
so a good name for the feature branch would be "feature/issue3456"

Create this new branch in GitHub from the master branch.


### Look at the configuration

All dependencies of a docker image are configured in the file [dockerbuild-config.yaml](automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml).

For the Secretsmanagement-Operator this is:

```
...
secretsmanagement-operator:  
  displayName: SecretsManagement-Operator
  fileName: secretsmanagement-operator

  valuesYamlFile: charts/canvas-oda/values.yaml
  valuesPathImage: .secretsmanagement-operator.image
  valuesPathVersion: .secretsmanagement-operator.version
  valuesPathPrereleaseSuffix: .secretsmanagement-operator.prereleaseSuffix

  paths:
  - source/operators/secretsmanagementOperator-hc/docker/**/*
  buildContext: source/operators/secretsmanagementOperator-hc/docker
  # default is "Dockerfile" in buildContext
  #buildDockerfile:
  # default is "linux/amd64,linux/arm64"
  platforms: linux/amd64 # linux/arm64 has problems building cffi python wheel
```

The relevant information for us now are the location and names in the values YAML file and the location of the source paths.
Whenever a file/folder which is referenced in "paths:" is changed a docker build is triggered on pushing the changes to github.


### Configure Prerelease-Version in values.yaml

Currently the values.yaml file has the following entries:

```
...
secretsmanagement-operator:
  image: tmforumodacanvas/secretsmanagement-operator
  version: 0.1.0
  prereleaseSuffix:
  ...
```

The corresponding dockerfile is `tmforumodacanvas/secretsmanagement-operator:0.1.0`.
We want to do a small change, so just increment the patch level and add a prereleaseSuffix: `tmforumodacanvas/secretsmanagement-operator:0.1.1-issue-3456`
So, the version and prereleaseSuffix entries have to be changed:

```
...
secretsmanagement-operator:
  image: tmforumodacanvas/secretsmanagement-operator
  version: 0.1.1
  prereleaseSuffix: issue3456
  ...
```

(Make sure, no one else uses the same prerelease version otherwise You will overwrite each others docker image)


### Change the code

From the configuration, we can see, that the sources are in the folder `source/operators/secretsmanagementOperator-hc/docker`.
Any change in this folder will trigger a new build of the dockerimage with tag 0.1.1-issue3456.







## How-To add a new Dockerimage

TODO[FH]: Describe

Edit `automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml`

Execute `automation/generators/dockerbuild-workflow-generator/dockerbuild_workflow_generator.py`


