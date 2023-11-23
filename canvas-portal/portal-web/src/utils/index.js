import request from "@/utils/request";
import path from '@/utils/path';
const api = {
    getComponents(params) {
        return request.get(path.getComponents, { params });
    },
    logOut() {
        return request.post(path.logOut);
    },
    getComponentInstance(params) {
        return request.get(path.getComponentInstance, { params });
    },
    getInstanceDetail(name, params) {
        return request.get(path.getInstanceDetail(name), { params });
    },
    getReleaseDetailInfo(release, params) {
        return request.get(path.getReleaseDetailInfo(release), { params });
    },
    getInstanceEvents(name, params) {
        return request.get(path.getInstanceEvents(name), { params });
    },
    getComponentApi(params) {
        return request.get(path.getComponentApi, { params });
    },
    getComponentResources(name, params) {
        return request.get(path.getComponentResources(name), { params });
    },
    getReleaseValues(release, params) {
        return request.get(path.getReleaseValues(release), { params });
    },
    getReleaseVersion(release, params) {
        return request.get(path.getReleaseVersion(release), { params });
    },
    getCharts(params) {
        return request.get(path.getCharts, { params });
    },
    getChartVersions(repoName, chartName, params) {
        return request.get(path.getChartVersions(repoName, chartName), { params });
    },
    getOrchestrations(params) {
        return request.get(path.getOrchestrations, { params });
    },
    installRelease(params) {
        return request.post(path.installRelease, params);
    },
    getChartValues(repoName, chartName, version) {
        return request.get(path.getChartValues(repoName, chartName, version));
    },
    uninstallRelease(release, namespace) {
        return request.delete(path.uninstallRelease(release, namespace));
    },
    getNamespace() {
        return request.get(path.getNamespace);
    }
}
export default api; 