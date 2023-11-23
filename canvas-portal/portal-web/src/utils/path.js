export default {
    logOut: 'logout',
    getComponents: 'console/oda/instances/stats/domain',
    getComponentInstance: 'console/oda/instances/summary',
    getInstanceDetail: name => `console/oda/instances/${name}/summary`,
    getReleaseDetailInfo: release => `console/helm/releases/${release}/detail`,
    getInstanceEvents: name => `console/oda/instances/${name}/events`,
    getComponentApi: 'console/oda/apis',
    getComponentResources: name => `console/oda/instances/${name}/resources`,
    getReleaseValues: release => `console/helm/releases/${release}/values`,
    getReleaseVersion: release => `console/helm/releases/${release}/revisions`,
    getCharts: 'console/helm/charts',
    getChartVersions: (repoName, chartName) => `console/helm/charts/${repoName}/${chartName}/versions`,
    getOrchestrations: `console/oda/orchestrations`,
    installRelease: 'console/helm/releases',
    getChartValues: (repoName, chartName, version) => `console/helm/charts/${repoName}/${chartName}/${version}/values`,
    uninstallRelease: (release, namespace) => `console/helm/releases/${release}/uninstall?namespace=${namespace}`,
    getNamespace: 'console/oda/namespaces'
}