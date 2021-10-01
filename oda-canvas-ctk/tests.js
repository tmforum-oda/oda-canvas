const k8s = require('@kubernetes/client-node')
const chai = require('chai')
var expect = chai.expect
const request = require('request')

console.log('********************************************************')
console.log('Open Digital Architecture - Canvas Test Kit CTK v1alpha1')
console.log('********************************************************')
console.log()

const kc = new k8s.KubeConfig()
kc.loadFromDefault()
const opts = {};
kc.applyToRequest(opts);
const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api)
const k8sVersionAPI = kc.makeApiClient(k8s.VersionApi)

describe("Basic Kubernetes checks", function () {
    it("Can connect to the cluster", function (done) {
        k8sCoreApi.listNode().then((res) => {
            expect(res.body).to.not.be.null
            done()
        }).catch(done)
    })
    
    const supportedVersions = ['v1.18', 'v1.19', 'v1.20', 'v1.21', 'v1.22']
    it("Cluster is running a supported version: " + supportedVersions, function (done) {
        k8sVersionAPI.getCode().then((res) => {
            // console.log(res.body)
            let clusterVersion = "v" + res.body.major + "." + res.body.minor
            expect(clusterVersion).to.be.oneOf(supportedVersions, "'clusterVersion' must be within supported versions " + supportedVersions)
            done()
        }).catch(done)
    })

    it("Cluster is running 3 control plane nodes", function (done) {
        k8sCoreApi.listNode().then((res) => {
            let validNodeLabels = ['node-role.kubernetes.io/master', 'node-role.kubernetes.io/control-plane']
            let controlPlaneNodes = res.body.items.filter(element => {
                let nodeLabels = JSON.stringify(element.metadata.labels, null, 2)
                return validNodeLabels.some(element => nodeLabels.includes(element))
            })
            expect(controlPlaneNodes, "Number of control plane nodes").to.have.length(3)
            done()
        }).catch(done)
    })

    it("Cluster is running at least 2 worker nodes", function (done) {
        k8sCoreApi.listNode().then((res) => {
            let invalidNodeLabels = ['node-role.kubernetes.io/master', 'node-role.kubernetes.io/control-plane']
            let workerNodes = res.body.items.filter(element => {
                let nodeLabels = JSON.stringify(element.metadata.labels, null, 2)
                return invalidNodeLabels.some(element => !nodeLabels.includes(element))
            })
            expect(workerNodes, "Number of worker nodes").to.have.lengthOf.above(2)
            done()
        }).catch(done)
    })
})

describe("Canvas namespace checks", function () {
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
})

describe("Canvas custom resource definitions", function () {
    it("oda.tmforum.org/v1alpha3 APIs CRD exists", function (done) {
        request.get(`${kc.getCurrentCluster().server}/apis/oda.tmforum.org/v1alpha3/namespaces/*/apis`, opts,
            (error, response, body) => {
                if (error) {
                    // console.log(`error: ${error}`)
                }
                if (response) {
                    // console.log(`statusCode: ${response.statusCode}`)
                }
                // console.log(`body: ${body}`)
                expect(response.statusCode, "API response code").to.equal(200)
                done()
            })
    })
    it("oda.tmforum.org/v1alpha3 Components CRD exists", function (done) {
        request.get(`${kc.getCurrentCluster().server}/apis/oda.tmforum.org/v1alpha3/namespaces/*/components`, opts,
            (error, response, body) => {
                if (error) {
                    // console.log(`error: ${error}`)
                }
                if (response) {
                    // console.log(`statusCode: ${response.statusCode}`)
                }
                // console.log(`body: ${body}`)
                expect(response.statusCode, "API response code").to.equal(200)
                done()
            })
    })
    it("zalando.org/v1 Kopfpeerings CRD exists", function (done) {
        request.get(`${kc.getCurrentCluster().server}/apis/zalando.org/v1/namespaces/*/kopfpeerings`, opts,
            (error, response, body) => {
                if (error) {
                    // console.log(`error: ${error}`)
                }
                if (response) {
                    // console.log(`statusCode: ${response.statusCode}`)
                }
                // console.log(`body: ${body}`)
                expect(response.statusCode, "API response code").to.equal(200)
                done()
            })
    })
    it("zalando.org/v1 Clusterkopfpeerings CRD exists", function (done) {
        request.get(`${kc.getCurrentCluster().server}/apis/zalando.org/v1/clusterkopfpeerings`, opts,
            (error, response, body) => {
                if (error) {
                    // console.log(`error: ${error}`)
                }
                if (response) {
                    // console.log(`statusCode: ${response.statusCode}`)
                }
                // console.log(`body: ${body}`)
                expect(response.statusCode, "API response code").to.equal(200)
                done()
            })
    })
})