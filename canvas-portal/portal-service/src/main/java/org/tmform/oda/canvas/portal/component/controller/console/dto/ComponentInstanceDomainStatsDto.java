package org.tmform.oda.canvas.portal.component.controller.console.dto;

import java.util.List;

import org.tmform.oda.canvas.portal.component.service.console.oda.ComponentInstanceSummary;


/**
 *
 * ODA组件实例按Domain统计
 *
 * @author li.peilong
 * @date 2022/12/12
 */
public class ComponentInstanceDomainStatsDto {
    private String domain;
    private List<OdaComponentTypeInstance> types;

    public String getDomain() {
        return domain;
    }

    public void setDomain(String domain) {
        this.domain = domain;
    }

    public List<OdaComponentTypeInstance> getTypes() {
        return types;
    }

    public void setTypes(List<OdaComponentTypeInstance> types) {
        this.types = types;
    }

    public static class OdaComponentTypeInstance {
        private String type;

        private List<ComponentInstanceSummary> instances;

        public String getType() {
            return type;
        }

        public void setType(String type) {
            this.type = type;
        }

        public List<ComponentInstanceSummary> getInstances() {
            return instances;
        }

        public void setInstances(List<ComponentInstanceSummary> instances) {
            this.instances = instances;
        }
    }
}

