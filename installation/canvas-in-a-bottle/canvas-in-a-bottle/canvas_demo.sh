#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NOCOLOR='\033[0m' # No Color

echo "
....................................................................................................
....................................................................................................
.................................................................................***********........
..............................................................................**************........
.............@@@@*...........................................................,**********,,,,........
.............@@@@*...........................................................********,..............
.............@@@@*...........................................................********...............
.......@@@@@@@@@@@@@@@@@....&@@@@/....,@@@@@@%............&@@@@@@/..,**************************.....
.......@@@@@@@@@@@@@@@@@....&@@@@/,@@@@@@@@@@@@@@@...*@@@@@@@@@@@@@@@&.,********************........
.............@@@@*..........&@@@@@@@@@......@@@@@@@@@@@@@%.....,@@@@@@@#.*****************..........
.............@@@@*..........&@@@@@@.........../@@@@@@@@...........&@@@@@/....********...............
.............@@@@*..........&@@@@@.............%@@@@@@.............@@@@@@....********...............
.............@@@@*..........&@@@@(..............@@@@@@.............%@@@@@....********...............
.............@@@@*..........&@@@@/..............@@@@@@.............%@@@@@....********...............
.............@@@@*..........&@@@@/..............@@@@@@.............%@@@@@....********...............
.............@@@@*..........&@@@@/..............@@@@@@.............%@@@@@....********...............
.............@@@@%..........&@@@@/..............@@@@@@.............%@@@@@....********...............
.............@@@@@@@,.......&@@@@/..............@@@@@@.............%@@@@@....********...............
...............@@@@@@@@@@@..&@@@@/..............@@@@@@.............%@@@@@....********...............
.................,..,/((/,...................................................,......................
....................................................................................................
....................................................................................................

╔═╗┌─┐┌┐┌┬  ┬┌─┐┌─┐  ┬┌┐┌  ┌─┐  ┌┐ ┌─┐┌┬┐┌┬┐┬  ┌─┐
║  ├─┤│││└┐┌┘├─┤└─┐  ││││  ├─┤  ├┴┐│ │ │  │ │  ├┤ 
╚═╝┴ ┴┘└┘ └┘ ┴ ┴└─┘  ┴┘└┘  ┴ ┴  └─┘└─┘ ┴  ┴ ┴─┘└─┘

"

echo "
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@ ...........................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,@@@@@@@@@@@@@@@@@@@@@@@@@
@@,,,................................/........#,........................,,,,,@@@@@@@@@@@@@@@@@@@@@@@
@(,,..........................,,,,,,(*/,,,,,,/*/,,,,,.....................,,,,,@@@@@@@@@@@@@@@@@@@@@
@,,,.........................*                     (*.......................,,,,@@@@@@@@@@@@@@@@@@@@
@,,..........................*      ****.***,      #*........................,,,,(@@@@@@@@@@@@@@@@@@
@,,..........................*    ***. * *  **.    #*.........................,,,,,@@@@@@@@@@@@@@@@@
@,,........................../    ****, * *.***    #*...........................,,,,,@@@@@@@@@@@@@@@
.,,..........................*    ***,. *  ****    /*..............................,,,,,,(@@,,,,%@@@
.,,..........................*      *********      **.....................................(#((((((((
.,,..........................(, /,                 ,*.....................................((((#(((((
.,,..........................*/ /                  ,*.....................................(#((((##((
.,,..........................****.,,.((( ,,,((/ /(,.*.....................................****,,@@@@
@,,...............................,//***********/(/.*.............................,,,,@@@@@@,,,,@@@@
@,,................................**/....**.*/................................,,,,,@@@@@@@@@@@@@@@@
@,,...............................***.....**..*/..............................,,,,@@@@@@@@@@@@@@@@@@
@,,,.............................***......*/..(**............................,,,,@@@@@@@@@@@@@@@@@@@
@,,,............................***.......*/...***.........................,,,,,@@@@@@@@@@@@@@@@@@@@
@(,,...........................***........*/....*/........................,,,,@@@@@@@@@@@@@@@@@@@@@@
@@,,,............................................*/..................,,,,,,,,@@@@@@@@@@@@@@@@@@@@@@@
@@@,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@((((((((((((((((((((((((((((((((((((((((((((((((((@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@((((((((((((((((((((((((((((((((((((((((((((((((((((@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@####@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@####&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
"

export PS1="\[\e]0;\u@tmf-canvas-in-a-bottle: \w\a\]${debian_chroot:+($debian_chroot)}\u@tmf-canvas-in-a-bottle:\w\$ "

echo Bringing up a cluster
bash -c '/usr/local/bin/kind delete cluster'
bash -c '/usr/local/bin/kind create cluster'
mkdir /root/logs

echo Modifying Kubernetes config to point to Kind master node
MASTER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kind-control-plane)
sed -i "s/^    server:.*/    server: https:\/\/$MASTER_IP:6443/" $HOME/.kube/config
docker network connect kind tmf-canvas-in-a-bottle
cd

echo -e ${BLUE}
echo =====================================================================
echo Deploying Kubernetes dashboard and create a dashboard service account
echo =====================================================================
echo -e ${NOCOLOR}
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.4.0/aio/deploy/recommended.yaml > /root/logs/dashboard.log
kubectl create serviceaccount dashboard-admin-sa > /root/logs/dashboard.log
kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa > /root/logs/dashboard.log

echo Setting up Kubectl Proxy
CLIENT_IP=$(docker inspect --format '{{ .NetworkSettings.Networks.kind.IPAddress }}' tmf-canvas-in-a-bottle)
kubectl proxy --address=$CLIENT_IP --accept-hosts=^localhost$,^127\.0\.0\.1$,^\[::1\]$ &
secret=$(kubectl get secrets | awk '/dashboard-admin-sa/{print $1}') &


echo -e ${BLUE}
echo ===========================
echo You can access the Kuberbetes Dashboard at:
echo http://127.0.0.1:30303/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
echo -e ${GREEN}
echo -e The Secret for accessing Kubernetes Dashboard can be found by issuing the following command:
echo -e "     get_dashboard_token "
echo ===========================
echo -e ${NOCOLOR}

echo -e ${BLUE}
echo ===========================
echo Deploying Grafana Dashboard
echo ===========================
echo -e ${NOCOLOR}
kubectl create namespace grafana > /root/logs/grafana.log
helm repo add stable https://charts.helm.sh/stable > /root/logs/grafana.log
helm repo add grafana https://grafana.github.io/helm-charts > /root/logs/grafana.log
helm install --namespace grafana grafana grafana/grafana > /root/logs/grafana.log


for ((tsecs = 1; tsecs <= 300; tsecs++)); do
    export POD_NAME=$(kubectl get pods --namespace grafana -o jsonpath="{.items[0].metadata.name}")
    if [[ $(kubectl get pods --namespace grafana $POD_NAME -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') == "True" ]]; then
        echo OK
        echo Set up port forwarding for Grafana
        kubectl --namespace grafana port-forward --address $CLIENT_IP $POD_NAME 3000:3000 &
        echo -e ${BLUE}
        echo ===============================================================
        echo You can access the Grafana dashboard at the following location:
        echo -e ${GREEN}
        echo http://127.0.0.1:3000
        echo -e ${BLUE}
        echo You will be prompted for a login username/password. To get the
        echo username/password credentials, run the following script:
        echo -e ${GREEN}
        echo -e "    get_grafana_credentials"
        echo -e ${BLUE}
        echo ==================================================================
        echo -e ${NOCOLOR}
        break
    else
        echo -n ". " && sleep 1;
    fi       
done

echo -e ${BLUE}
echo ===========================
echo Deploying Istio
echo ===========================
echo -e ${NOCOLOR}
istioctl install --set profile=demo -y > /root/logs/istio.log

echo -e ${BLUE}
echo ====================================================
echo Deploying TMF Canvas
echo ====================================================
echo
echo ----------------------------------------------------
cat <<EOF
Installing Canvas:
  Running script to:
    1. Install cluster enablers
    2. Install Reference Implementation services
    3. Install the Canvas
EOF
echo ----------------------------------------------------
echo -e ${NOCOLOR}
cd /root/oda-canvas-charts
helm install oda-ri-enablers clusterenablers/ > /root/logs/canvasInstall.log
cd ReferenceImplementation/cert-manager
chmod 700 install_cert-manager.sh 
./install_cert-manager.sh  > /root/logs/canvasInstall.log
cd /root/oda-canvas-charts
chmod 700 install_canvas_cert-manager.sh 
./install_canvas_cert-manager.sh  > /root/logs/canvasInstall.log

cd
/bin/bash

# Clean up cluster after exit from shell
kind delete cluster

