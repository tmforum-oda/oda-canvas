package org.tmforum.oda.canvas.portal.helm.client.operation.chart;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;

/**
 * Chart file
 *
 * @author li.peilong
 * @date 2023/02/04
 */
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChartFile {
    private String name;
    private Boolean directory;
    private Long size;

    /**
     * file relative path
     */
    private String path;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Boolean getDirectory() {
        return directory;
    }

    public void setDirectory(Boolean directory) {
        this.directory = directory;
    }

    public Long getSize() {
        return size;
    }

    public void setSize(Long size) {
        this.size = size;
    }

    public String getPath() {
        return path;
    }

    public void setPath(String path) {
        this.path = path;
    }
}
