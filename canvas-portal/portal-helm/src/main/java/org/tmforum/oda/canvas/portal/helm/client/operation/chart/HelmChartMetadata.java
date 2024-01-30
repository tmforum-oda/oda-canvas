package org.tmforum.oda.canvas.portal.helm.client.operation.chart;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.google.common.base.Splitter;
import org.apache.commons.lang3.StringUtils;

import java.util.List;
import java.util.Map;

/**
 * Helm Chart metadata info
 *
 * @author liu.jiang
 * @date 2022/11/23 10:55
 * @see "chart.metadata.go"
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class HelmChartMetadata {
    // 组成：repoName/chartName
    private String name;
    private String repoName;
    private String chartName;
    // A SemVer 2 conformant version string of the chart. Required.
    private String version;
    // A one-sentence description of the chart
    private String description;
    // The version of the application enclosed inside of this chart.
    private String appVersion;
    // The API Version of this chart. Required.
    private String apiVersion;
    // KubeVersion is a SemVer constraint specifying the version of Kubernetes required.
    private String kubeVersion;
    // Specifies the chart type: application or library
    private String type;
    // The URL to a relevant project page, git repo, or contact person
    private String home;
    // The URL to an icon file.
    private String icon;
    // Dependencies are a list of dependencies for a chart.
    private List<Dependency> dependencies;
    // A list of string keywords
    private List<String> keywords;
    // A list of name and URL/email address combinations for the maintainer(s)
    private List<Maintainer> maintainers;
    // Annotations are additional mappings uninterpreted by Helm,
    // made available for inspection by other applications.
    private Map<String, String> annotations;
    // Source is the URL to the source code of this chart
    private List<String> sources;

    public String getRepoName() {
        if (StringUtils.isNotEmpty(repoName)) {
            return repoName;
        }
        // extract from name
        if (StringUtils.isNotEmpty(name) && name.contains("/")) {
            repoName = Splitter.on("/").limit(2).splitToList(name).get(0);
        }
        return repoName;
    }

    public void setRepoName(String repoName) {
        this.repoName = repoName;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getAppVersion() {
        return appVersion;
    }

    public void setAppVersion(String appVersion) {
        this.appVersion = appVersion;
    }

    public String getChartName() {
        if (StringUtils.isNotEmpty(chartName)) {
            return chartName;
        }
        // 从name中提取
        if (StringUtils.isNotEmpty(name) && name.contains("/")) {
            chartName = Splitter.on("/").limit(2).splitToList(name).get(1);
        }
        return chartName;
    }

    public void setChartName(String chartName) {
        this.chartName = chartName;
    }

    public List<String> getKeywords() {
        return keywords;
    }

    public void setKeywords(List<String> keywords) {
        this.keywords = keywords;
    }

    public List<Maintainer> getMaintainers() {
        return maintainers;
    }

    public void setMaintainers(List<Maintainer> maintainers) {
        this.maintainers = maintainers;
    }

    public String getApiVersion() {
        return apiVersion;
    }

    public void setApiVersion(String apiVersion) {
        this.apiVersion = apiVersion;
    }

    public String getHome() {
        return home;
    }

    public void setHome(String home) {
        this.home = home;
    }

    public String getIcon() {
        return icon;
    }

    public void setIcon(String icon) {
        this.icon = icon;
    }

    public List<String> getSources() {
        return sources;
    }

    public void setSources(List<String> sources) {
        this.sources = sources;
    }

    public List<Dependency> getDependencies() {
        return dependencies;
    }

    public void setDependencies(List<Dependency> dependencies) {
        this.dependencies = dependencies;
    }

    public String getKubeVersion() {
        return kubeVersion;
    }

    public void setKubeVersion(String kubeVersion) {
        this.kubeVersion = kubeVersion;
    }

    public String getType() {
        if (StringUtils.isBlank(type)) {
            this.type = "application";
        }
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public Map<String, String> getAnnotations() {
        return annotations;
    }

    public void setAnnotations(Map<String, String> annotations) {
        this.annotations = annotations;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Dependency {
        private String name;
        private String version;

        private String repository;
        private String condition;

        private List<String> tags;
        private List<String> importValues;
        private String alisa;



        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getRepository() {
            return repository;
        }

        public void setRepository(String repository) {
            this.repository = repository;
        }

        public List<String> getTags() {
            return tags;
        }

        public void setTags(List<String> tags) {
            this.tags = tags;
        }

        public String getVersion() {
            return version;
        }

        public void setVersion(String version) {
            this.version = version;
        }

        public String getCondition() {
            return condition;
        }

        public void setCondition(String condition) {
            this.condition = condition;
        }

        public List<String> getImportValues() {
            return importValues;
        }

        public void setImportValues(List<String> importValues) {
            this.importValues = importValues;
        }

        public String getAlisa() {
            return alisa;
        }

        public void setAlisa(String alisa) {
            this.alisa = alisa;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Maintainer {
        private String name;
        private String email;
        private String url;

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getUrl() {
            return url;
        }

        public void setUrl(String url) {
            this.url = url;
        }

        public String getEmail() {
            return email;
        }

        public void setEmail(String email) {
            this.email = email;
        }
    }
}
