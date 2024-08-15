# Developer How-Tos: Work with Dockerimages

The project oda-canvas is configured to automatically build docker images, when their source code is changed.
To successfully collaborate in the same repository some rules have to be followed.

## Global Rules

* Release versions (image tags) follow the semantic versioning format "\<major\>.\<minor\>.\<increment\>" and are built only from the master branch
* Release versions are immutable and can not be overwritten 
* Prerelease versions have the format "\<major\>.\<minor\>.\<increment\>-\<prerelease-suffix\>" and are built from feature branches
* Feature branches have the format "feature/\*" or "odaa-\*"
* Prerelease versions are overwritten every time the source code changed
* The prerelease suffix should be unique for each feature branch, otherwise the same image will be built from different branches and the last build wins
* Versions are stored in the charts/canvas-oda/values.yaml file which is also used for deploying the canvas-oda chart (single source of truth)

## Versions in values.yaml

Dockerimages are versioned in the [charts/canvas-oda/values.yaml](../../charts/canvas-oda/values.yaml) file of the canva-oda chart and consist of three parts. 
E.g. for oda-webhook:

```
...
oda-webhook:
  image: tmforumodacanvas/compcrdwebhook
  version: 0.6.3
  prereleaseSuffix: issue123
```

The full dockerimage is put together as "tmforumodacanvas/compcrdwebhook:0.6.3-issue123".

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
that when deploying the canvas-oda chart from the filesystem all docker images exist, because they are automatically build on code changes.

A prerelease version is semantically smaller than the release version:

```
0.6.2 < 0.6.3-issue-123 < 0.6.3
```

How this can be used to implement a workflow is shown in the following example updating the secretsmanagement-operator.

## Example: Update code of Secretsmanagement-Operator

### Step 1: Create a feature branch 

To do your code changes a feature branch is needed.
Feature branches have the naming convention "feature/..." or "odaa-...".
Let´s assume we are working on the GitHub issue 3456, 
so a good name for the feature branch would be "feature/issue3456"

Create this new branch in GitHub from the master branch.

### Step 2: Configure Prerelease Version in feature branch

First get an overview, how the Dockerfile for the secretsmanagement-operator is built

#### Look at the Docker build configuration

All dependencies of a Docker image are configured in the file [automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml](../../automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml).

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
  platforms: linux/amd64 
```

The relevant information for us now are the location and names in the values YAML file and the location of the source paths.
Whenever a file/folder, which is referenced in "paths", is changed a docker build is triggered when pushing changes to github.


#### Configure Prerelease-Version in values.yaml

Currently the values.yaml file has the following entries:

```
...
secretsmanagement-operator:
  image: tmforumodacanvas/secretsmanagement-operator
  version: 0.1.0
  prereleaseSuffix:
  ...
```

The corresponding docker image name is `tmforumodacanvas/secretsmanagement-operator:0.1.0`.
We want to do a small change, so just increment the patch level and add a prereleaseSuffix.
The "version" and "prereleaseSuffix" entries have to be changed in the feature branch accordingly:

```
...
secretsmanagement-operator:
  image: tmforumodacanvas/secretsmanagement-operator
  version: 0.1.1
  prereleaseSuffix: issue3456
  ...
```
This would result in a docker image named: `tmforumodacanvas/secretsmanagement-operator:0.1.1-issue3456`

(Make sure, no one else uses the same prerelease version otherwise you will overwrite each others docker image.)


### Step 3: Change the code in the feature branch

From the docker build configuration above, we can see, that the sources are in the folder `source/operators/secretsmanagementOperator-hc/docker`.
Any change in this folder will trigger a new build of the dockerimage with tag `0.1.1-issue3456`.

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

So, two files were changed, the `values.yaml` with the version number and an additional log line in the `secretsmanagementOperatorHC.py`:

![image](https://github.com/user-attachments/assets/419d3e5f-d593-47b1-88a4-c83f76715779)

### Step 4: Push changed feature branch to GitHub

Comitting the changes in the feature branch locally and pushing them to the GitHub repository triggers a GitHub Action, which builds the docker prerelease image.

![image](https://github.com/user-attachments/assets/d264d6c5-6933-4932-9e31-16323d87aa69)

If we had not set a prereleaseSuffix, then the build would have fail with the error message, that release versions can only be built from the "master" branch.

But as we set a prereleaseSuffix a new image with tag `0.1.1-issue3456` was created and uploaded to dockerhub:

| ![image](https://github.com/user-attachments/assets/2bfff74b-d0fc-4c43-a472-3cac75d66d74) |
|-|

Now we have an up to date dockerimage and can upgrade the canvas.

### Step 5: Upgrade Canvas

We will deploy the canvas update from the helm chart `oda-canvas` in the filesystem.

#### Update chart dependencies

If it was not done before, the chart dependencies have to be updated.

From the command line in the root of the locally checked out repository execute the following commands:

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

Now we are ready to install/upgrade the canvas.

#### Install/Upgrade canvas

Again from the root of the local git repository execute the following command:

```
$ helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace 

  Release "canvas" has been upgraded. Happy Helming!
  NAME: canvas
  LAST DEPLOYED: Tue Jul 30 16:23:41 2024
  NAMESPACE: canvas
  STATUS: deployed
  REVISION: 2
```

The next time when an upgrade has to be deployed the dependencies do not have to be updated/built again.

### Step 5: Test that changed code is active

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

So, our change is active, the line `GitHub ISSUE #3456 was added here` is logged out on startup of the secretsmanagement-operator.

Most of the time you need more than one iteration to get your code functional.
So an iterative process of code changes is neccessary.

### Step 6a..6n: Modify code multiple times

In our example we will modify the same file again source/operators/secretsmanagementOperator-hc/docker/secretsmanagementOperatorHC.py:

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

Committing and pushing the new code changes in the feature branch triggers again the GitHub Action to build the Docker file.

![image](https://github.com/user-attachments/assets/9427ac1e-f0c8-4aed-b9e9-1792e942a07d)

Wait until the build was successfully finished (green hook), then update the canvas deployment:

#### Update canvas deployment

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

#### Look for the changes in the logfile

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

_*Our change is not visible!!!*_

We can see in the Logfile, the `CICD_BUILD_TIME`, the `GIT_COMMIT_SHA` and also the timestamp when the log was written. 
This is not our latest build and also the time when the log was written is the same as before the canvas redeployment.
This means, the secretsmanagement-operator was not updated.

Our deployment did not change and the dockerimage name also not, it is still `tmforumodacanvas/secretsmanagement-operator:0.1.1-issue3456`.

So, Kubernetes did not see any reason to redeploy the SecretsManagement-Operator.
When we did the first upgrade, the docker image changed from `...:0.1.0` to `...:0.1.1-issue3456` and that triggered a redeployment of the secretsmanagement-operator.
Now the image did not change, it is still `...:0.1.1-issue3456`.

But we can trigger a redeployment manually:

```
$ kubectl rollout restart deployment -n canvas canvas-smanop

  deployment.apps/canvas-smanop restarted
```

Waiting a few seconds to give the old POD (running instance of the deployment) time to gracefully terminate and the new POD time to startup:

```
$ kubectl get pods -n canvas

  NAME                                          READY   STATUS      RESTARTS   AGE
  ...
  canvas-smanop-6768cc66b5-ww85z                1/1     Running     0          8s
  ...
```

Age 8 seconds means, the POD was just started. Now we can take a look into the logfile:

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

The log timestamps are updated, so the log was newly written, but the second line is still the old one!

This really came as a surprise for me. I expected the docker image to be repulled.
In the charts we have configured the deployments in a way, that prerelease images automatically get the imagePullPolicy "Always".
This means, even if a  docker image with the same name already exists it is looking for updates in the remote docker registry.

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

I have no explanation, why this did not work, but found a workaround:
Scaling the deployment down to 0 instances (PODs) and then scaling up to 1 again:

```
$ kubectl scale deployment -n canvas canvas-smanop --replicas=0
  deployment.apps/canvas-smanop scaled

$ kubectl scale deployment -n canvas canvas-smanop --replicas=1
  deployment.apps/canvas-smanop scaled
```

Wait a few seconds for the new POD to come up and look at the logfile:

```
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

As we can see the `GIT_COMMIT_SHA` (short version, only the first 7 digits of the complete GIT SHA) we can verify, 
if the version deployed is realy the version we pushed.
To verify the `GIT_COMMIT_SHA` you can use the git cli command:

```
$ git rev-parse --short HEAD
  462b37e
```

Sidenote: instead of scaling the deployment to zero and up again, it is also possible to delete the running PODs. 
Then the new docker image is also pullled.

### Step 7: Creating a Pull-Request

After the iterative process of doing code changes, and testing the image, we are ready to contribute our changes back to the "master" branch.

Therefore a Pull-Request (PR) is created from our feature branch `feature/issue-3456` into "master" using GitHub UI.

#### Automatically Run Tests

Now the automatic tests of the PR are triggered and the result should be green. (WIP)

#### Check for release versions

Additionally there is a check, that no prereleaseSuffixes are set in the values.yaml.
For our PR this check fails, because secretsmanagement-operator has prereleaseSuffix "issue3456".

![image](https://github.com/user-attachments/assets/41a329e2-7b8b-4373-bd05-58cb2883ca72)

| ![image](https://github.com/user-attachments/assets/30099789-3643-4b49-909a-0b3af1ae9081) |
|-|

This can be solved by removing the prereleaseSuffix in the values.yaml:

```
...
secretsmanagement-operator:
    image: ocfork/secretsmanagement-operator
    version: 0.1.1
[*] prereleaseSuffix:
    ...
```

After pushing this change, the two checks (Linting and Release version check) are triggered again:

![image](https://github.com/user-attachments/assets/e687ec09-df02-4eea-b347-d09cbbb72f32)

A docker build was not triggered again, because there was no change in the docker source files.
Now all preconditions are green:

![image](https://github.com/user-attachments/assets/9842c0b2-f353-4c42-bc23-bcd47f7d426c)


### Step 8: Code-Review and Merging the PR

A code review can now be done and after appoval the branch can be merged into the "master" branch.

When the PR is merged, the release build of the docker image is triggered:

![image](https://github.com/user-attachments/assets/3e0ffa45-cb22-413b-8135-6e9aa360708b)

There is a check, that the release version does not already exists.
If this is the case, the build pipeline will fail.

But here, everything is fine and the build is successful:

![image](https://github.com/user-attachments/assets/754e2284-31d1-42f6-ad3f-315f68663fd8)

In the Docker registry there is now a release version 0.1.1:

| ![image](https://github.com/user-attachments/assets/afbe328e-9492-44e3-93c0-ac6ae4879774) |
|-|

# Summary

Overview about the steps to do:

* Create feature branch "feature/..." and do all work in this branch
* Increment version number and set prereleaseSuffix for Dockerimage to modify in [charts/canvas-oda/values.yaml](../../charts/canvas-oda/values.yaml)
* Modify code, push triggers rebuild of prerelease docker image
* For the first time do a `helm upgrade` to redeploy the prerelease version
* For any further modifications to a `kubectl scale deployment ... ---replicas 0` and then `kubectl scale deployment ... ---replicas 1` (or delete running PODs)
* Finally create PR and make BDD tests green
* Remove prereleaseSuffixes from values.yaml
* Merge the PR

# How-To add a new Dockerimage

Currently there are 6 Docker images which are built automatically.
New Docker images can be added by editing the file [automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml](../../automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml).
In this file the docker build specific configurations and the relevant source paths have to be set.

After the configuration is finished, the GitHub Actions have to be regenerated 
by executing [automation/generators/dockerbuild-workflow-generator/dockerbuild_workflow_generator.py](../../automation/generators/dockerbuild-workflow-generator/dockerbuild_workflow_generator.py). For executing the python script, the packages "pyyaml" and "jinja2" have to be installed (see requirements.txt).
