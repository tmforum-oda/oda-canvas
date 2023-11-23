package org.tmforum.oda.canvas.portal.helm.client.operation.release;


import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Date;

/**
 * @author liu.jiang
 * @date 2022/11/23 15:05
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class HelmRelease {
    private String name;

    private String namespace;

    private Integer revision;

    private Date updated;

    // unknown,deployed,uninstalled,superseded,failed,uninstalling,pending-install,pending-upgrade,pending-rollback
    private String status;

    private String chart;

    @JsonProperty("app_version")
    private String appVersion;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getNamespace() {
        return namespace;
    }

    public void setNamespace(String namespace) {
        this.namespace = namespace;
    }

    public Integer getRevision() {
        return revision;
    }

    public void setRevision(Integer revision) {
        this.revision = revision;
    }

    public Date getUpdated() {
        return updated;
    }

    public void setUpdated(Date updated) {
        this.updated = updated;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getChart() {
        return chart;
    }

    public void setChart(String chart) {
        this.chart = chart;
    }

    public String getAppVersion() {
        return appVersion;
    }

    public void setAppVersion(String appVersion) {
        this.appVersion = appVersion;
    }
}
