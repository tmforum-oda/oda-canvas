package org.tmforum.oda.canvas.portal.helm;

import java.util.Date;

import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmRelease;

/**
 * Details of helm release
 *
 * @author li.peilong
 * @date 2023/02/13
 */
public class HelmReleaseDetail extends HelmRelease {
    private String chartName;
    private String repoName;
    private String chartVersion;
    private Date firstDeployed;
    private Date lastDeployed;
    private String description;

    public String getChartName() {
        return chartName;
    }

    public void setChartName(String chartName) {
        this.chartName = chartName;
    }

    public String getRepoName() {
        return repoName;
    }

    public void setRepoName(String repoName) {
        this.repoName = repoName;
    }

    public String getChartVersion() {
        return chartVersion;
    }

    public void setChartVersion(String chartVersion) {
        this.chartVersion = chartVersion;
    }

    public Date getFirstDeployed() {
        return firstDeployed;
    }

    public void setFirstDeployed(Date firstDeployed) {
        this.firstDeployed = firstDeployed;
    }

    public Date getLastDeployed() {
        return lastDeployed;
    }

    public void setLastDeployed(Date lastDeployed) {
        this.lastDeployed = lastDeployed;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}
