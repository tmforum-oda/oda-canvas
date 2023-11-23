package org.tmform.oda.canvas.portal.component.service.console.helm;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.util.JsonUtil;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;

/**
 * 在helm release中记录一些额外的信息，比如chart的仓库，名称等
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
     * 返回Base64编码的字符串
     *
     * @return
     */
    public String toBase64String() throws BaseAppException {
        return Base64.getEncoder().encodeToString(JsonUtil.object2Json(this).getBytes(StandardCharsets.UTF_8));
    }


    /**
     * 从release的description中构造对象
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
