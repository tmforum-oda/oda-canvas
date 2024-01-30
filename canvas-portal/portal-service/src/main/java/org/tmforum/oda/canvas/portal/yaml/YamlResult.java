package org.tmforum.oda.canvas.portal.yaml;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;

/**
 * 包含YAML的结果
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class YamlResult {
    private String data;

    public String getData() {
        return data;
    }

    public void setData(String data) {
        this.data = data;
    }
}
