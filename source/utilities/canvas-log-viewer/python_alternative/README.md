# Python Canvas Log Viewer

this is an alternative to the node.js Canvas Log Viewer

## Installation

A Python installation with package `rich` installed is needed.
An existing environment can be used, or as described here,
a new Python environment can be setup

### Setup Python environment

```
mkdir -p ~/.venv
python3 -m venv ~/.venv/canvaslogs
. ~/.venv/canvaslogs/bin/activate
pip install rich
```

### create plugin for kubectl

if needed adjust the python path in kubectl-canvaslogs. 
It assumes the virtual environment in ~/.venv/canvaslogs

copy binaries into an installation folder

```
mkdir -p ~/canvaslogs
cp kubectl-canvaslogs ~/canvaslogs/
cp showlogtree.py ~/canvaslogs/
chmod a+x ~/canvaslogs/kubectl-canvaslogs
```

create symbolic link to executable (or add ~/canvaslogs to PATH env var)

```
sudo ln -s ~/canvaslogs/kubectl-canvaslogs /usr/local/bin/kubectl-canvaslogs
```

### test

```
$ kubectl canvaslogs

  usage: kubectl canvaslogs (comp|sman|depapi) [componentfilter]
         needs python with 'pip install rich'
```

## Usage

```
kubectl canvaslogs comp
```

shows the complete log of the Component-Operator

```
kubectl canvaslogs sman demo-a-productcatalogmanagement
```

shows the SecretsManagement-Operator logs related to the component `demo-a-productcatalogmanagement`

```
kubectl canvaslogs depapi *-productcatalog*
```

shows the DependentAPI-Operator logs related to components matching the pattern `*-productcatalog*`



