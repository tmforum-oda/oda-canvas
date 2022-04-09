const { execSync, spawn, spawnSync, exec } = require('child_process');
const fs = require('fs');
const yaml = require('js-yaml')
const apiMapping = require('../utils/apiMapping.json')
const k8s = require('@kubernetes/client-node');



export default function handler(req, res) {
    if (req.method === 'POST') {


        var body = JSON.parse(req.body)
        if (body['cleanUp']) { 
            try {
                logs += execSync("/usr/local/bin/kind delete cluster")
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
        }

        if (body['kind']) {
            console.log(body)
            var masterIP = ""
            var clientIP = ""
            var logs = ""
            
            try {
                logs += execSync(`cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
- |-
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:5000"]
    endpoint = ["http://kind-registry:5000"]
EOF`)
                logs += execSync(`if [ "$(docker inspect -f='{{json .NetworkSettings.Networks.kind}}' "kind-registry")" = 'null' ]; then
docker network connect "kind" "kind-registry"
fi`)

            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
            try {
                masterIP = execSync("docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kind-control-plane")
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }

            var kubeConfig;
            try {
                let kubeConfigFile = fs.readFileSync('/root/.kube/config', 'utf8');
                kubeConfig = yaml.load(kubeConfigFile);
                //console.log(JSON.stringify(kubeConfig, null, 4))
                console.log(masterIP.toString())
                kubeConfig.clusters.forEach(cluster => {
                    //console.log(JSON.stringify(cluster['cluster']['server'], null, 4))
                    cluster['cluster']['server'] = `https://${masterIP.toString().replace('\n','')}:6443`

                });
                //console.log(JSON.stringify(kubeConfig, null, 4))
                fs.writeFileSync('/root/.kube/config', yaml.dump(kubeConfig))
            } catch (e) {
                console.log('ERROR while loading Kube config' + e)
                res.status(500).json({ "data": null, "error": JSON.stringify(e), "logs": logs })
                return;
            }



            try {

                execSync('docker network connect kind tmf-canvas-in-a-bottle', (error, stdout, stderr) => {
                    if (error) {
                        console.error(`execSync error: ${error}`);
                        //res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                        //return;
                    }
                    else {
                        logs += stdout
                    }

                });
                logs += execSync(`
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
    name: local-registry-hosting
    namespace: kube-public
data:
    localRegistryHosting.v1: |
    host: "localhost:5000"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF
                `)
            } catch (e) {
                console.log(e)
            }


        }
        const kc = new k8s.KubeConfig();
        kc.loadFromDefault();
        const k8sApi = kc.makeApiClient(k8s.CoreV1Api);
        if (body['dashboard']) {
            try {
                logs += execSync("kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.4.0/aio/deploy/recommended.yaml")
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }

            try {
                logs += execSync("kubectl create serviceaccount dashboard-admin-sa")
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
            try {
                logs += execSync("kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa")
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
            try {
                clientIP += execSync("docker inspect --format '{{ .NetworkSettings.Networks.kind.IPAddress }}' tmf-canvas-in-a-bottle")
                console.log("CLIENT IP: " + clientIP)
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
            try {
                var child = spawn('/usr/local/bin/kubectl', ['port-forward', 'service/kubernetes-dashboard', '-n', 'kubernetes-dashboard', '8443:443'], {
                    slient:true,
                    detached:true,
                    stdio: [null, null, null, 'ipc']
                  });
                child.unref();
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
        }
        if (body['canvas']) {
            try {
                logs += execSync("istioctl install --set profile=demo -y")
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
            try {
                logs += execSync("helm install oda-ri-enablers clusterenablers/", {cwd: '/root/oda-canvas-charts'})
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
            try {
                logs += execSync("./install_cert-manager.sh", {cwd: '/root/oda-canvas-charts/ReferenceImplementation/cert-manager'})
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
            try {
                logs += execSync("./install_canvas_cert-manager.sh ", {cwd: '/root/oda-canvas-charts'})
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
        }
        if (body['installReferenceAPIs'] && body['individualAPIs']) { 
            console.log(JSON.stringify(body['individualAPIs']))
            body['individualAPIs'].forEach(api => {
                apiMapping[api]
            });
            try {
                k8sApi.listNamespacedPod('default').then((res) => {
                    console.log(res.body);
                });
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
        }
        if (body['useCaseToggle'] && body['useCaseController']) { 
            console.log(JSON.stringify(body['useCaseController']))
            body['useCaseController'].forEach(uc => {
                console.log(uc)
            });
            try {
                k8sApi.listNamespacedPod('default').then((res) => {
                    console.log(res.body);
                });
            }

            catch (error) {
                console.error(`execSync error: ${error}`);
                res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
                return;
            }
        }
        console.log(logs)
        res.status(200).json({ "data": "", "logs": logs, "error": null })

    } else {
        res.status(501).json({})
    }

}