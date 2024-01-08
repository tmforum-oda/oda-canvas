package org.tmforum.oda.canvas.portal.component.service.console.oda;

import com.google.common.base.Splitter;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;

import java.util.List;

import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChart;

/**
 * ODA组件模板
 *
 * @author li.peilong
 * @date 2023/02/06
 */
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Component {
    public static final Component NULL = Component.builder().build();
    private String name;
    private String version;
    private String type;
    private String domain;
    private String vendor;
    private String description;
    private String chartName;
    private String repoName;
    private String chartVersion;

    /**
     * 将helm chart转换成ODA组件模板
     *
     * @param chart
     * @return
     */
    public static Component from(HelmChart chart) {
        if (chart == null) {
            return NULL;
        }
        String chartName = chart.getChartName();
        // TODO: 约定ODA组件的chart名组成：[vendor name]-[product name]-[oda type]
        //暂时不校验
        List<String> parts = Splitter.on("-").splitToList(chartName);

        ComponentType type = ComponentType.unknown;
        String vendor = "--";
        if (parts.size() == 3) {
            type = ComponentType.from(parts.get(2));
            vendor = parts.get(0);
            // 返回一个空对象
//            return NULL;
        }
//        OdaComponentType type = OdaComponentType.from(parts.get(2));
//        String vendor = parts.get(0);
        return Component.builder()
            .name(chartName)
            .type(type.getName())
            .domain(type.getDomain())
            .vendor(vendor)
            .version(chart.getAppVersion())
            .description(chart.getDescription())
            .chartName(chartName)
            .repoName(chart.getRepoName())
            .chartVersion(chart.getVersion())
            .build();
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

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getDomain() {
        return domain;
    }

    public void setDomain(String domain) {
        this.domain = domain;
    }

    public String getVendor() {
        return vendor;
    }

    public void setVendor(String vendor) {
        this.vendor = vendor;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

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
}
