package org.tmforum.oda.canvas.portal.component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;

/**
 * Canvas component
 *
 * @author li.peilong
 * @Date 2022/12/12
 */
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CanvasComponent {
    private String name;
    private Type type;
    private String version;
    private Boolean ready = Boolean.FALSE;

    public Type getType() {
        return type;
    }

    public void setType(Type type) {
        this.type = type;
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

    public Boolean getReady() {
        return ready;
    }

    public void setReady(Boolean ready) {
        this.ready = ready;
    }

    public enum Type {
        API_GATEWAY("apig"),
        SERVICE_MESH("istio"),
        LOAD_BALANCER,
        LICENSE_MANAGER;
        private final List<String> charts;

        Type(String... charts) {
            this.charts = new ArrayList<>();
            if (charts != null) {
                this.charts.addAll(Arrays.asList(charts));
            }
        }

        public List<String> getCharts() {
            return charts;
        }
    }
}
