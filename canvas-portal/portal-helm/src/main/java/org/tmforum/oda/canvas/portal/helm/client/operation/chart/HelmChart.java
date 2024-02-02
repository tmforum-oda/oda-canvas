package org.tmforum.oda.canvas.portal.helm.client.operation.chart;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.Splitter;
import org.apache.commons.lang3.StringUtils;

/**
 * @author liu.jiang
 * @date 2022/11/23 10:55
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class HelmChart {
    // format：repoName/chartName
    private String name;
    private String repoName;
    private String chartName;
    private String version;

    private String description;
    @JsonProperty("app_version")
    private String appVersion;

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

    public String getName() {
        return name;
    }

    public String getVersion() {
        return version;
    }

    public String getDescription() {
        return description;
    }

    public String getAppVersion() {
        return appVersion;
    }

    public String getChartName() {
        if (StringUtils.isNotEmpty(chartName)) {
            return chartName;
        }
        // extract from name
        if (StringUtils.isNotEmpty(name) && name.contains("/")) {
            chartName = Splitter.on("/").limit(2).splitToList(name).get(1);
        }
        return chartName;
    }

    public void setChartName(String chartName) {
        this.chartName = chartName;
    }

    public void setRepoName(String repoName) {
        this.repoName = repoName;
    }

    public void setName(String name) {
        this.name = name;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public void setAppVersion(String appVersion) {
        this.appVersion = appVersion;
    }
}
