# ODA Canvas Development Environment

This repository contains the development environment setup for the ODA Canvas project. The dev container definition included in this project allows you to easily run and develop the ODA Canvas, including running the compliance-test-kit.

## Prerequisites

Before you can start using the dev container, make sure you have the following prerequisites installed:

- [Docker](https://www.docker.com/get-started)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Open the project in Visual Studio Code with the option "Open in container".

## Getting Started

To get started with the ODA Canvas development environment, follow these steps:

1. Clone this repository to your local machine:

   ```bash
   $ git clone https://github.com/your-username/oda-canvas.git
   ```

2. Open the cloned repository in Visual Studio Code:

   ```bash
   $ cd oda-canvas
   $ code .
   ```

3. Visual Studio Code will detect the dev container configuration and prompt you to reopen the project in a container. Click on "Reopen in Container" to start the development environment.

4. Once the dev container is built and the development environment is ready, you can run the test-kit by executing the following command in the integrated terminal:

```bash
$ gcloud auth login --no-browser

You are authorizing gcloud CLI without access to a web browser. Please run the following command on a machine with a web browser and copy its output back here. Make sure the installed gcloud version is 372.0.0 or newer.

gcloud auth login --remote-bootstrap="https://accounts.google.com/o/oauth2/auth?response_type=code&...&token_usage=remote"


Enter the output of the above command: 
```

Copy the `gcloud` command line into another terminal and execute it. A browser will open where you may have to select a google account and (on a further page) allow the access. The browser it than forwarded to a localhost address which will fail to load. Nevertheless you have to copy&paste the url (`https://localhost:8085/...`) into terminal used before. After you are logged in and can give the project a name.

```bash
(link is shorten here)

Enter the output of the above command: https://localhost:8085/?state=...&scope=email%20openid%20https://www.googleapis.com/auth/userinfo.email%20https://www.googleapis.com/auth/cloud-platform%20https://www.googleapis.com/auth/appengine.admin%20https://www.googleapis.com/auth/sqlservice.login%20https://www.googleapis.com/auth/compute%20https://www.googleapis.com/auth/accounts.reauth&authuser=0&prompt=consent

You are now logged in as [xxxxxxxxxxxxx].
Your current project is [None].  You can change this setting by running:
  $ gcloud config set project PROJECT_ID

$ gcloud config set project tmf-ihc
```

5. Install the `google-cloud-sdk-gke-gcloud-auth-plugin` by running the following command:

```bash
$ sudo apt-get update && sudo apt-get install google-cloud-sdk-gke-gcloud-auth-plugin
```

6. Generate a kubeconfig entry 

- goto th Google Cloud console -> Kubernetes Engine -> Clusters -> click on the cluster you want to use -> click on CONNECT -> copy the shown command line `gcloud container clusters ...`
- run the copied command line in a console/terminal outside of VSC

```bash
$ gcloud container clusters get-credentials innovation-hub-cluster --zone europe-west4-b --project tmforum-oda-component-cluster
Fetching cluster endpoint and auth data.
kubeconfig entry generated for innovation-hub-cluster.

$ $ kubectl config get-contexts (Note: the console output has been shortened)
CURRENT   NAME                                             CLUSTER                   AUTHINFO                  NAMESPACE
*         gke_tmforum-oda-comp..._innovation-hub-cluster   gke_tmforum-oda-comp...   gke_tmforum-oda-comp...   
```

7. Optionally, you can rename the context to make it easier to handle:

```bash
$ kubectl config rename-context gke_tmforum-oda-component-cluster_europe-west4-b_innovation-hub-cluster tmf-ihc
```

8. Now follow the [CTK readme](compliance-test-kit/BDD-and-TDD/README.md#how-to-run-the-tests)