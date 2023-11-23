package org.tmforum.oda.canvas.portal.helm.client.operation.repo;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/**
 * @author liu.jiang
 * @date 2022/12/1
 * @time 14:40
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class HelmRepo {
    private String name;

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
}
