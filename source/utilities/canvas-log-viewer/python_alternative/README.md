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
pip install rich timedinput
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


usage: kubectl canvaslogs [-f] (comp|sman|depapi|apiistio|idconf|credman) [<componentfilter>] [-l <last-hours>]
       needs python with 'pip install rich timedinput'

options:
  -h, (help)          show this help message and exit
  <component-filter>  filter components by name with wildcards (*/?), e.g. "comp-a-*"
  -f, (follow)        keep the Log Viewer open and update the display on incoming logs
  -l <last-hours>     only look at the last n hours in logfile

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
kubectl canvaslogs depapi *-productcatalog* -l8
```

shows the DependentAPI-Operator logs related to components matching the pattern `*-productcatalog*` filtered for the last 8 hours.
Please be aware, that there might be a timeshift (server time to local time)

```
kubectl canvaslogs -f apiistio 
```

shows the Api-Operator-Istio logs and follows new logs. To cancel this press <Ctrl>-C.




