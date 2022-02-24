const { execSync, spawn, spawnSync } = require('child_process');
const fs = require('fs');
const yaml = require('js-yaml')

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
                logs += execSync("/usr/local/bin/kind create cluster")
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
                console.log("MASTER IP: " + stdout)
                return;
            }

            var kubeConfig;
            try {
                let kubeConfigFile = fs.readFileSync('/root/.kube/config', 'utf8');
                kubeConfig = yaml.load(kubeConfigFile);
                //console.log(JSON.stringify(kubeConfig, null, 4))
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



            // try {
            //     execSync('docker network connect kind tmf-canvas-in-a-bottle', (error, stdout, stderr) => {
            //         if (error) {
            //             console.error(`execSync error: ${error}`);
            //             //res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
            //             //return;
            //         }
            //         else {
            //             logs += stdout
            //         }

            //     });
            // } catch (e) {
            //     console.log(e)
            // }


        }
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
        console.log(logs)
        res.status(200).json({ "data": "", "logs": logs, "error": null })

    } else {
        res.status(501).json({})
    }

}