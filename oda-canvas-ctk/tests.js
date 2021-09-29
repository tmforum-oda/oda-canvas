const k8s = require('@kubernetes/client-node')
const chai = require('chai')
let expect = chai.expect

console.log('********************************************************')
console.log('Open Digital Architecture - Canvas Test Kit CTK v1alpha1')
console.log('********************************************************')
console.log()

const kc = new k8s.KubeConfig()
kc.loadFromDefault()
const k8sApi = kc.makeApiClient(k8s.CoreV1Api)

describe("Basic Kubernetes checks", function () {
    it("Can connect to the cluster", function (done) {
        k8sApi.listNode().then((res) => {
            expect(res.body).to.not.be.null
            done()
        }).catch(done)
    })
    
    const supportedVersions = ['v1.22.2', 'v1.22.0', 'v1.22.1']
    it("Kubelet version is within supported versions: " + supportedVersions, function (done) {
        k8sApi.listNode().then((res) => {
            res.body.items.forEach(element => {
                const kubeletVersion = element.status.nodeInfo.kubeletVersion
                expect(kubeletVersion).to.be.oneOf(supportedVersions, "'kubeletVersion' should be within supported versions " + supportedVersions)
                done()
            })
        }).catch(done)
    })
})
