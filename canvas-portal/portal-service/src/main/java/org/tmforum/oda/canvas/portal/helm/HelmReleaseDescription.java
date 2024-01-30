package org.tmforum.oda.canvas.portal.helm;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.util.JsonUtil;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;

/**
 * Records some additional information in a helm release, such as the repository, name, etc., of the chart.
 *
 * @author li.peilong
 * @date 2023/02/13
 */
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HelmReleaseDescription {
    private String repoName;
    private String chartName;
    private String chartVersion;
    private String description;

    /**
     * Returns a Base64 encoded string.
     *
     * @return
     */
    public String toBase64String() throws BaseAppException {
        return Base64.getEncoder().encodeToString(JsonUtil.object2Json(this).getBytes(StandardCharsets.UTF_8));
    }

    /**
     * Constructs an object from the release's description.
     *
     * @return
     */
    public static HelmReleaseDescription from(String description) {
        try {
            return JsonUtil.json2Object(new String(Base64.getDecoder().decode(description), StandardCharsets.UTF_8), HelmReleaseDescription.class);
        }
        catch (Exception e) {
            return HelmReleaseDescription.builder().description(description).build();
        }
    }

    public String getRepoName() {
        return repoName;
    }

    public void setRepoName(String repoName) {
        this.repoName = repoName;
    }

    public String getChartName() {
        return chartName;
    }

    public void setChartName(String chartName) {
        this.chartName = chartName;
    }

    public String getChartVersion() {
        return chartVersion;
    }

    public void setChartVersion(String chartVersion) {
        this.chartVersion = chartVersion;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}
