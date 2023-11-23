package org.tmforum.oda.canvas.portal.helm.client.operation.release;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Date;

/**
 * Release状态
 *
 * @author li.peilong
 * @date 2023/02/13
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class HelmReleaseStatus {
    private String name;
    private String namespace;
    @JsonProperty("first_deployed")
    private Date firstDeployed;
    @JsonProperty("last_deployed")
    private Date lastDeployed;
    private String status;
    private String description;

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

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

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
}
