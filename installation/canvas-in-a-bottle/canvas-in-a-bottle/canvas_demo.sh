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

export PS1="\[\e]0;\u@secretless-k8s-demo: \w\a\]${debian_chroot:+($debian_chroot)}\u@secretless-k8s-demo:\w\$ "

echo Bringing up a cluster
bash -c '/usr/local/bin/kind create cluster'

echo Modifying Kubernetes config to point to Kind master node
MASTER_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kind-control-plane)
sed -i "s/^    server:.*/    server: https:\/\/$MASTER_IP:6443/" $HOME/.kube/config
cd

echo -e ${BLUE}
echo =====================================================================
echo Deploying Kubernetes dashboard and create a dashboard service account
echo =====================================================================
echo -e ${NOCOLOR}
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-rc3/aio/deploy/recommended.yaml
kubectl create serviceaccount dashboard-admin-sa
kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa

echo Setting up Kubectl Proxy
CLIENT_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' secretless-demo-client)
kubectl proxy --address=$CLIENT_IP --accept-hosts=^localhost$,^127\.0\.0\.1$,^\[::1\]$ &

echo -e ${BLUE}
echo ===========================
echo Deploying Grafana Dashboard
echo ===========================
echo -e ${NOCOLOR}
kubectl create namespace grafana
helm repo add stable https://kubernetes-charts.storage.googleapis.com
helm install --namespace grafana my-release stable/grafana

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
helm install oda-ri-enablers clusterenablers/ 
cd ReferenceImplementation/cert-manager
chmod 700 install_cert-manager.sh
./install_cert-manager.sh
cd /root/oda-canvas-charts
chmod 700 install_canvas_cert-manager.sh
./install_canvas_cert-manager.sh

echo -e ${BLUE}
echo ----------------------------------------------------
cat <<EOF
Application Developer Setup:
  Running script to:
    1. Configure the application to connect to PostgreSQL via Secretless
    2. Deploy the application and the Secretless sidecar
    3. Test the application
EOF
echo ----------------------------------------------------
echo -e ${NOCOLOR}
./02_app_developer_steps

# Test application will be exposed on NodePort 30970
# TODO: May have to use a worker node IP for multi-node operation
# TODO: Use -o go-template and set up a temlate to read application nodePort.
NODE_PORT=$(kubectl get svc -n quick-start-application-ns quick-start-application -o yaml | awk '/nodePort/{print $3}')
export APPLICATION_URL=$MASTER_IP:$NODE_PORT

echo -e ${BLUE}
echo ====================================================
echo The Secretless Broker Kubernetes demo is running!!!
echo ====================================================
echo -e ${NOCOLOR}
echo A "Pet Store" application pod has been deployed that
echo contains both an application container and a CyberArk Secretless
echo Broker sidecar container. The Secretless Broker sidecar container
echo allows the application to connect to a password-protected Postgres
echo database without any knowledge of database credentials!!!
echo
echo To see the Kubernetes resources that have been configured,
echo start with the following commands:
echo -e ${GREEN}
echo "    kubectl get namespaces"
echo "    kubectl get all -n quick-start-application-ns"
echo "    kubectl get all -n quick-start-backend-ns"
echo -e ${NOCOLOR}
echo To see the CyberArk Secretless Broker in action, use the scripts
echo in /root to create and list pets in the pet store:
echo -e ${GREEN}
echo "    add_pet \"Genghis D. Dog\""
echo "    add_pet \"Miss Ava\""
echo "    add_pet \"Mr. Roboto\""
echo "    list_pets"
echo -e ${BLUE}
echo ====================================================
echo -e ${NOCOLOR}

echo -e ${BLUE}
echo ==================================================================
echo You can access the Kubernetes dashboard at the following location:
echo -e ${GREEN}
echo http://127.0.0.1:30303/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
echo -e ${BLUE}
echo You will be prompted for login credentials. Run the following script
echo to display the dashboard access token:
echo -e ${GREEN}
echo -e "    get_dashboard_token"
echo -e ${BLUE}
echo ==================================================================
echo -e ${NOCOLOR}
echo "Waiting for Grafana pod to become ready"
export POD_NAME=$(kubectl get pods --namespace grafana -l "app=grafana,release=my-release" -o jsonpath="{.items[0].metadata.name}")
for ((tsecs = 1; tsecs <= 300; tsecs++)); do
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
    fi
    echo -n ". " && sleep 1;
done

# Start up a bash shell to try out Secretless
cd
/bin/bash

# Clean up cluster after exit from shell
kind delete cluster --name secretless-kube

