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


### Look at the Docker image configuration

All dependencies of a Docker image are configured in the file [dockerbuild-config.yaml](automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml).

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
We want to do a small change, so just increment the patch level and add a prereleaseSuffix: `tmforumodacanvas/secretsmanagement-operator:0.1.1-issue3456`
The version and prereleaseSuffix entries have to be changed accordingly:

```
...
secretsmanagement-operator:
  image: tmforumodacanvas/secretsmanagement-operator
  version: 0.1.1
  prereleaseSuffix: issue3456
  ...
```

(Make sure, no one else uses the same prerelease version otherwise You will overwrite each others docker image)


### Change the code in the feature branch

From the configuration, we can see, that the sources are in the folder `source/operators/secretsmanagementOperator-hc/docker`.
Any change in this folder will trigger a new build of the dockerimage with tag 0.1.1-issue3456.

For now just let´s add one print line on startup of the SecretsManagement-Operator:

https://github.com/tmforum-oda/oda-canvas/blob/32e89708912b2fb170f268efccdccb4325fb25ab/source/operators/secretsmanagementOperator-hc/docker/secretsmanagementOperatorHC.py#L38

```
    # Setup logging
    logging_level = os.environ.get("LOGGING", logging.INFO)
    kopf_logger = logging.getLogger()
    kopf_logger.setLevel(logging.WARNING)
    logger = logging.getLogger("SecretsmanagementOperator")
    logger.setLevel(int(logging_level))
    logger.info(f"Logging set to %s", logging_level)
[+] logger.info(f"GitHub ISSUE #3456 was added here")
    logger.debug(f"debug logging active")
```

So, two files were changed, the values.yaml with the version number and an additional log line in the secretsmanagementOperatorHC.py:

![image](https://github.com/user-attachments/assets/419d3e5f-d593-47b1-88a4-c83f76715779)

Pushing the changes to github triggeres the docker build of the prerelease image.

![Screenshot 2024-07-30 143203](https://github.com/user-attachments/assets/46a6cc5a-9de8-44dc-a45e-5919bcdff093)

If we would not have added a prereleaseSuffix, then the build will fail with an error message, that release versions can only be built from the master branch.

But as we set a prereleaseSuffix a new image was created:

![image](https://github.com/user-attachments/assets/2bfff74b-d0fc-4c43-a472-3cac75d66d74)

Now we can upgrade our deployed canvas.

### Upgrade Canvas

The Canvas can now be upgraded (or installed new) using the helm chart.

#### Update chart dependencies

If this was not done before, all dependencies of the canvas-oda chart have to be updated:

```
cd charts/cert-manager-init
helm dependency update
helm dependency build
cd ../../charts/controller
helm dependency update
helm dependency build
cd ../../charts/canvas-vault
helm dependency update
helm dependency build
cd ../../charts/secretsmanagement-operator
helm dependency update
helm dependency build
cd ../../charts/canvas-oda
helm dependency update
helm dependency build
cd ../..
```

Now we can install/upgrade the canvas using helm:

```
$ helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace 

  Release "canvas" has been upgraded. Happy Helming!
  NAME: canvas
  LAST DEPLOYED: Tue Jul 30 16:23:41 2024
  NAMESPACE: canvas
  STATUS: deployed
  REVISION: 2
```

The next time, when an upgrade has to be deployed, the dependencies do not have to be updated/built again.

### Check the changed code is active

Let´s take a look at the SecretsManagement-Operator logfile:

```
$ kubectl logs -n canvas deployment/canvas-smanop

    [2024-07-30 14:24:20,772] SecretsmanagementOpe [INFO    ] Logging set to 20
[*] [2024-07-30 14:24:20,773] SecretsmanagementOpe [INFO    ] GitHub ISSUE #3456 was added here
    [2024-07-30 14:24:20,773] SecretsmanagementOpe [INFO    ] SOURCE_DATE_EPOCH=1722342693
    [2024-07-30 14:24:20,773] SecretsmanagementOpe [INFO    ] GIT_COMMIT_SHA=7dfc477
    [2024-07-30 14:24:20,773] SecretsmanagementOpe [INFO    ] CICD_BUILD_TIME=2024-07-30T12:32:02+00:00
    [2024-07-30 14:24:20,779] SecretsmanagementOpe [WARNING ] Environment variable HVAC_TOKEN given as plaintext. 
    Please remove HVAC_TOKEN variable and use HVAC_TOKEN_ENC: gAAAAABmqPeU7O_WFBHu8UcBL1dA7FOmujM1UZocV23PxB9ka4SEszb3dYokUkJUc40BbZUB2Qyi_tDkEd3bc3IHJJZsz7hmhQ==
```

So, our changes are already active!

### Changing the code a second time

Now we tested our changes and decided to once again change the code in the feature branch.
Modify the code again in source/operators/secretsmanagementOperator-hc/docker/secretsmanagementOperatorHC.py:

```
    # Setup logging
    logging_level = os.environ.get("LOGGING", logging.INFO)
    kopf_logger = logging.getLogger()
    kopf_logger.setLevel(logging.WARNING)
    logger = logging.getLogger("SecretsmanagementOperator")
    logger.setLevel(int(logging_level))
    logger.info(f"Logging set to %s", logging_level)
[*] logger.info(f"GitHub ISSUE #3456 WAS FIXED!!!")
    logger.debug(f"debug logging active")
```

Committing and pushing the code triggers again the GitHub Action to build the Docker file.

![image](https://github.com/user-attachments/assets/9427ac1e-f0c8-4aed-b9e9-1792e942a07d)

Wait until the build was successfully finished (green bullet), then update the canvas deployment:

### update canvas deployment 2nd time

We do not need to update all the dependency again, so just calling `helm upgrade ...` is sufficient:

```
$ helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace

  Release "canvas" has been upgraded. Happy Helming!
  NAME: canvas
  LAST DEPLOYED: Tue Jul 30 16:23:41 2024
  NAMESPACE: canvas
  STATUS: deployed
  REVISION: 3
```

### Look for the changes in the logfile

```
kubectl logs -n canvas deployment/canvas-smanop

    [2024-07-30 14:24:20,772] SecretsmanagementOpe [INFO    ] Logging set to 20
[?] [2024-07-30 14:24:20,773] SecretsmanagementOpe [INFO    ] GitHub ISSUE #3456 was added here
    [2024-07-30 14:24:20,773] SecretsmanagementOpe [INFO    ] SOURCE_DATE_EPOCH=1722342693
    [2024-07-30 14:24:20,773] SecretsmanagementOpe [INFO    ] GIT_COMMIT_SHA=7dfc477
    [2024-07-30 14:24:20,773] SecretsmanagementOpe [INFO    ] CICD_BUILD_TIME=2024-07-30T12:32:02+00:00
    [2024-07-30 14:24:20,779] SecretsmanagementOpe [WARNING ] Environment variable HVAC_TOKEN given as plaintext.
    Please remove HVAC_TOKEN variable and use HVAC_TOKEN_ENC:
    gAAAAABmqPeU7O_WFBHu8UcBL1dA7FOmujM1UZocV23PxB9ka4SEszb3dYokUkJUc40BbZUB2Qyi_tDkEd3bc3IHJJZsz7hmhQ==
```

*Our change is not visible!!!*

We can see in the Logfile, the CICD_BUILD_TIME, the GIT_COMMIT_SHA and also the timestamp of the log. 
This is not our latest build and also the time of the log is the same as before the canvas redeployment.
Because our deployment did not change and the dockerimage name also is still the same `tmforumodacanvas/secretsmanagement-operator:0.1.1-issue3456`
Kubernetes had no need to redeploy the SecretsManagement-Operator.

Last time the docker image changed from "...:0.1.0" to "...:0.1.1-issue3456" and that triggered a redeployment of the secretsmanagement-operator.
Now the image did not change, it is still "...:0.1.1-issue3456".

But we can trigger a redeployment manually:

```
$ kubectl rollout restart deployment -n canvas canvas-smanop

  deployment.apps/canvas-smanop restarted
```

Waiting a few seconds to give the old POD time to gracefully terminate and the new POD time to startup:

```
$ kubectl get pods -n canvas

  NAME                                          READY   STATUS      RESTARTS   AGE
  ...
  canvas-smanop-6768cc66b5-ww85z                1/1     Running     0          8s
  ...
```

Age 8 seconds means, the POD was just started

Again a look into the logfile:

```
$ kubectl logs -n canvas canvas-smanop-7d4c875878-xdlts

    [2024-07-30 15:22:02,025] SecretsmanagementOpe [INFO    ] Logging set to 20
[?] [2024-07-30 15:22:02,025] SecretsmanagementOpe [INFO    ] GitHub ISSUE #3456 was added here
    [2024-07-30 15:22:02,025] SecretsmanagementOpe [INFO    ] SOURCE_DATE_EPOCH=1722342693
    [2024-07-30 15:22:02,025] SecretsmanagementOpe [INFO    ] GIT_COMMIT_SHA=7dfc477
    [2024-07-30 15:22:02,026] SecretsmanagementOpe [INFO    ] CICD_BUILD_TIME=2024-07-30T12:32:02+00:00
    [2024-07-30 15:22:02,030] SecretsmanagementOpe [WARNING ] Environment variable HVAC_TOKEN given as plaintext.
    Please remove HVAC_TOKEN variable and use HVAC_TOKEN_ENC:
    gAAAAABmqQUa2nvJFaSX27nAhyflGSnmnvA5Aw0gwLa0NjsnK9bbjx-RPPBexroeYHKiCoHUmd0pxiFyHRgtJBkzuw3w8b4_Jw==
```

This really came as a surprise for me. I expected the image to be repulled, 
because the imagePullPolicy for prerelease versions is automatically set to "Always".

Check:

```
$ kubectl get deployment -n canvas canvas-smanop -oyaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: canvas-smanop
  namespace: canvas
  ...
spec:
  strategy:
    type: Recreate
  template:
    spec:
      containers:
      - name: canvas-smanop
        image: ocfork/secretsmanagement-operator:0.1.1-issue3456
[*]     imagePullPolicy: Always
      ...
```

My understanding was, that with imagePullPolicy "Always", the image tage is repulled every time if there were changes (new SHA).
Maybe someone can explain this to me.

I found a workaround: Scaling the deployment down to 0 instances and then scaling up to 1 again:

```
$ kubectl scale deployment -n canvas canvas-smanop --replicas=0
  deployment.apps/canvas-smanop scaled

$ kubectl scale deployment -n canvas canvas-smanop --replicas=1
  deployment.apps/canvas-smanop scaled

$ kubectl logs -n canvas deployment/canvas-smanop
    [2024-07-30 15:31:14,306] SecretsmanagementOpe [INFO    ] Logging set to 20
[*] [2024-07-30 15:31:14,306] SecretsmanagementOpe [INFO    ] GitHub ISSUE #3456 WAS FIXED!!!
    [2024-07-30 15:31:14,306] SecretsmanagementOpe [INFO    ] SOURCE_DATE_EPOCH=1722351400
    [2024-07-30 15:31:14,306] SecretsmanagementOpe [INFO    ] GIT_COMMIT_SHA=462b37e
    [2024-07-30 15:31:14,307] SecretsmanagementOpe [INFO    ] CICD_BUILD_TIME=2024-07-30T14:57:04+00:00
    [2024-07-30 15:31:14,312] SecretsmanagementOpe [WARNING ] Environment variable HVAC_TOKEN given as plaintext.
    Please remove HVAC_TOKEN variable and use HVAC_TOKEN_ENC:
    gAAAAABmqQdCL8HcaLN2GJFP5gnAtJ0bXjaVFIWnw_ihXw-5U7pYFl-ieovQR3vGUyJvmKNDiZMP7R5IRPCtGkY8fJbAHpqJcw==
```

Now it is as expected. The changed code is active.
As the GIT_COMMIT_SHA ...









## How-To add a new Dockerimage

TODO[FH]: Describe

Edit `automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml`

Execute `automation/generators/dockerbuild-workflow-generator/dockerbuild_workflow_generator.py`


