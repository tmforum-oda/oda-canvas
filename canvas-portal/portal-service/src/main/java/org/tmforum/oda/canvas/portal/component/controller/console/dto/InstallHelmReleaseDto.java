package org.tmforum.oda.canvas.portal.component.controller.console.dto;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;

/**
 * 安装Helm Release DTO
 *
 * @author li.peilong
 * @date 2022/12/09
 */
public class InstallHelmReleaseDto {
    @NotNull
    private Integer tenantId;
    @NotBlank
    private String namespace;
    @NotBlank
    private String release;
    @NotBlank
    @Pattern(regexp = ".*/.*")
    private String chart;
    @NotBlank
    private String version;
    private String description;
    private String values;

    public String getChart() {
        return chart;
    }

    public void setChart(String chart) {
        this.chart = chart;
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

    public String getValues() {
        return values;
    }

    public void setValues(String values) {
        this.values = values;
    }

    public Integer getTenantId() {
        return tenantId;
    }

    public void setTenantId(Integer tenantId) {
        this.tenantId = tenantId;
    }

    public String getNamespace() {
        return namespace;
    }

    public void setNamespace(String namespace) {
        this.namespace = namespace;
    }

    public String getRelease() {
        return release;
    }

    public void setRelease(String release) {
        this.release = release;
    }
}
