const k8s = require('@kubernetes/client-node')
const chai = require('chai')
var expect = chai.expect
const request = require('request')
var mandatory_only = process.env.CANVAS_CTK_MANDATORY_ONLY;
var optional_keycloak = process.env.CANVAS_CTK_OPTIONAL_KEYCLOAK;
var optional_istio = process.env.CANVAS_CTK_OPTIONAL_ISTIO;
// process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0' // ignore self-signed certificate errors


const kc = new k8s.KubeConfig()
kc.loadFromDefault()
const opts = {};
kc.applyToRequest(opts);
const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api)
const k8sVersionAPI = kc.makeApiClient(k8s.VersionApi)
const k8sAppsAPI = kc.makeApiClient(k8s.AppsV1Api)
const ReleaseNamespace = 'canvas'

console.log()
console.log('********************************************************')
console.log('Open Digital Architecture - Canvas Test Kit CTK v1alpha1')
console.log('********************************************************')
console.log()

describe("Basic Kubernetes checks", function () {
    it("Can connect to the cluster", function (done) {
        k8sCoreApi.listNode().then((res) => {
            expect(res.body).to.not.be.null
            done()
        }).catch(done)
    })
    
    const supportedVersions = ['v1.22', 'v1.23', 'v1.24', 'v1.25', 'v1.26', 'v1.27', 'v1.28', 'v1.29']
    it("Cluster is running a supported kubernetes version: " + supportedVersions, function (done) {
        k8sVersionAPI.getCode().then((res) => {
            let clusterVersion = "v" + res.body.major + "." + res.body.minor
            expect(clusterVersion).to.be.oneOf(supportedVersions, clusterVersion + " must be within supported versions " + supportedVersions)
            done()
        }).catch(done)
    })

    // it("Cluster is running 3 control plane nodes", function (done) {
    //     k8sCoreApi.listNode().then((res) => {
    //         let validNodeLabels = ['node-role.kubernetes.io/master', 'node-role.kubernetes.io/control-plane', 'node-role.kubernetes.io/controlplane']
    //         let controlPlaneNodes = res.body.items.filter(element => {
    //             let nodeLabels = JSON.stringify(element.metadata.labels, null, 2)
    //             return validNodeLabels.some(element => nodeLabels.includes(element))
    //         })
    //         expect(controlPlaneNodes, "Number of control plane nodes").to.have.length(3)
    //         done()
    //     }).catch(done)
    // })

    // it("Cluster is running at least 2 worker nodes", function (done) {
    //     k8sCoreApi.listNode().then((res) => {
    //         let invalidNodeLabels = ['node-role.kubernetes.io/master', 'node-role.kubernetes.io/control-plane']
    //         let workerNodes = res.body.items.filter(element => {
    //             let nodeLabels = JSON.stringify(element.metadata.labels, null, 2)
    //             return invalidNodeLabels.some(element => !nodeLabels.includes(element))
    //         })
    //         expect(workerNodes, "Number of worker nodes").to.have.lengthOf.above(2)
    //         done()
    //     }).catch(done)
    // })
})

describe("Mandatory non-functional capabilities", function () {
    it("Canvas namespace exists", function (done) {
        k8sCoreApi.listNamespace().then((res) => {
            let namespaceArray = []
            res.body.items.forEach(element => namespaceArray.push(element.metadata.name))
            expect(namespaceArray, "Canvas namespace to be in list of namespaces").to.include('canvas')
            done()
        }).catch(done)
    })
    it("Components namespace exists", function (done) {
        k8sCoreApi.listNamespace().then((res) => {
            let namespaceArray = []
            res.body.items.forEach(element => namespaceArray.push(element.metadata.name))
            expect(namespaceArray, "Components namespace to be in list of namespaces").to.include('components')
            done()
        }).catch(done)
    })
    it("oda.tmforum.org/v1beta3 Components definition (CRD) exists", function (done) {
        request.get(`${kc.getCurrentCluster().server}/apis/oda.tmforum.org/v1beta3/namespaces/*/components`, opts,
            (error, response, body) => {
                expect(response.statusCode, "API response code").to.equal(200)
                done()
            })
    })
    it("oda.tmforum.org/v1beta3 APIs definition (CRD) exists", function (done) {
        request.get(`${kc.getCurrentCluster().server}/apis/oda.tmforum.org/v1beta3/namespaces/*/apis`, opts,
            (error, response, body) => {
                expect(response.statusCode, "API response code").to.equal(200)
                done()
            })
    })

    // These are implementation specific and should be moved to a separate test kit 
    // it("zalando.org/v1 Kopfpeerings CRD exists", function (done) {
    //    request.get(`${kc.getCurrentCluster().server}/apis/zalando.org/v1/namespaces/*/kopfpeerings`, opts,
    /*       (error, response, body) => {
                expect(response.statusCode, "API response code").to.equal(200)
                done()
            })
    })
    it("zalando.org/v1 Clusterkopfpeerings CRD exists", function (done) {
        request.get(`${kc.getCurrentCluster().server}/apis/zalando.org/v1/clusterkopfpeerings`, opts,
            (error, response, body) => {
                expect(response.statusCode, "API response code").to.equal(200)
                done()
            })
    })
    */

    it("Canvas operator is running", function (done) {
        k8sAppsAPI.readNamespacedDeploymentStatus('oda-controller', ReleaseNamespace).then((res) => {
            let unavailableReplicas = res.body.status.unavailableReplicas
            let readyReplicas = res.body.status.readyReplicas
            let replicas = res.body.status.replicas
            let availableReplicas = res.body.status.availableReplicas
            let updatedReplicas = res.body.status.updatedReplicas
            expect(unavailableReplicas, "Number of unavailable replicas").to.be.undefined &&
                expect(readyReplicas, "Number of ready replicas").to.deep.equal(replicas) &&
                expect(availableReplicas, "Number of available replicas").to.deep.equal(replicas) &&
                expect(updatedReplicas, "Number of up-to-date replicas").to.deep.equal(replicas)
            done()
        }).catch(done)
    })
    it("Canvas component versioning webhook is running", function (done) {
        k8sAppsAPI.readNamespacedDeploymentStatus('conversion-webhook', ReleaseNamespace).then((res) => {
            let unavailableReplicas = res.body.status.unavailableReplicas
            let readyReplicas = res.body.status.readyReplicas
            let replicas = res.body.status.replicas
            let availableReplicas = res.body.status.availableReplicas
            let updatedReplicas = res.body.status.updatedReplicas
            expect(unavailableReplicas, "Number of unavailable replicas").to.be.undefined &&
                expect(readyReplicas, "Number of ready replicas").to.deep.equal(replicas) &&
                expect(availableReplicas, "Number of available replicas").to.deep.equal(replicas) &&
                expect(updatedReplicas, "Number of up-to-date replicas").to.deep.equal(replicas)
            done()
        }).catch(done)
    })
})
if ((typeof optional_keycloak === 'undefined') && (typeof optional_istio === 'undefined')) {
    // force all the optional tests to run, as none have been specified
    var run_all_optional = true
}

if ( mandatory_only == 'true' ) {
    // do nothing - these are optional
    console.log(mandatory_only)
} else {
    describe("Optional non-functional capabilities", function () {
        if ((optional_keycloak == 'true') || (run_all_optional)) {
            it("Keycloak is running", function (done) {
                k8sAppsAPI.readNamespacedStatefulSetStatus('canvas-keycloak', ReleaseNamespace).then((res) => {
                    let readyReplicas = res.body.status.readyReplicas
                    let replicas = res.body.status.replicas
                    let updatedReplicas = res.body.status.updatedReplicas
                    expect(readyReplicas, "Number of ready replicas").to.deep.equal(replicas) &&
                        expect(updatedReplicas, "Number of up-to-date replicas").to.deep.equal(replicas)
                    done()
                }).catch(done)
            })
        }
        if ((optional_istio == 'true') || (run_all_optional)) {
            it("istio-system namespace exists", function (done) {
                k8sCoreApi.listNamespace().then((res) => {
                    let namespaceArray = []
                    res.body.items.forEach(element => namespaceArray.push(element.metadata.name))
                    expect(namespaceArray, "istio-system namespace to be in list of namespaces").to.include('istio-system')
                    done()
                }).catch(done)
            })
            it("istiod deployment is running", function (done) {
                k8sAppsAPI.readNamespacedDeploymentStatus('istiod', 'istio-system').then((res) => {
                    let unavailableReplicas = res.body.status.unavailableReplicas
                    let readyReplicas = res.body.status.readyReplicas
                    let replicas = res.body.status.replicas
                    let availableReplicas = res.body.status.availableReplicas
                    let updatedReplicas = res.body.status.updatedReplicas
                    expect(unavailableReplicas, "Number of unavailable replicas").to.be.undefined &&
                        expect(readyReplicas, "Number of ready replicas").to.deep.equal(replicas) &&
                        expect(availableReplicas, "Number of available replicas").to.deep.equal(replicas) &&
                        expect(updatedReplicas, "Number of up-to-date replicas").to.deep.equal(replicas)
                    done()
                }).catch(done)
            })
            it("istio-ingress gateway deployment is running", function (done) {
                k8sAppsAPI.readNamespacedDeploymentStatus('istio-ingress', 'istio-ingress').then((res) => {
                    let unavailableReplicas = res.body.status.unavailableReplicas
                    let readyReplicas = res.body.status.readyReplicas
                    let replicas = res.body.status.replicas
                    let availableReplicas = res.body.status.availableReplicas
                    let updatedReplicas = res.body.status.updatedReplicas
                    expect(unavailableReplicas, "Number of unavailable replicas").to.be.undefined &&
                        expect(readyReplicas, "Number of ready replicas").to.deep.equal(replicas) &&
                        expect(availableReplicas, "Number of available replicas").to.deep.equal(replicas) &&
                        expect(updatedReplicas, "Number of up-to-date replicas").to.deep.equal(replicas)
                    done()
                }).catch(done)
            })

            /*
            it("istio-egressgateway deployment is running", function (done) {
                k8sAppsAPI.readNamespacedDeploymentStatus('istio-egressgateway', 'istio-system').then((res) => {
                    let unavailableReplicas = res.body.status.unavailableReplicas
                    let readyReplicas = res.body.status.readyReplicas
                    let replicas = res.body.status.replicas
                    let availableReplicas = res.body.status.availableReplicas
                    let updatedReplicas = res.body.status.updatedReplicas
                    expect(unavailableReplicas, "Number of unavailable replicas").to.be.undefined &&
                        expect(readyReplicas, "Number of ready replicas").to.deep.equal(replicas) &&
                        expect(availableReplicas, "Number of available replicas").to.deep.equal(replicas) &&
                        expect(updatedReplicas, "Number of up-to-date replicas").to.deep.equal(replicas)
                    done()
                }).catch(done)
            }) */
        }
        
    })
}

