package org.tmform.oda.canvas.portal.component.service.console.helm;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

import org.apache.commons.io.FilenameUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.HelmClientUtil;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.ChartFile;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChart;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChartMetadata;

import com.google.common.base.Splitter;

/**
 * 提供Helm Chart相关服务
 *
 * @author li.peilong
 * @date 2022/12/09
 */
@Service
public class HelmChartService {
    @Autowired
    private HelmClient helmClient;
    @Autowired
    private HelmRepoService helmRepoService;
  
    /**
     * 获取Charts列表
     *
     * @param repoName 仓库名，需要是一个完成的仓库名称
     * @param keyword chart名称关键字
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> listCharts(String repoName, String keyword) throws BaseAppException {
        return helmClient.charts().list(repoName, keyword, false);
    }

    /**
     * 获取chart的版本列表
     *
     * @param name 要查询版本的chart，格式：reponame/chartname
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> listVersions(String name) throws BaseAppException {
        return helmClient.charts().versions(name);
    }

    /**
     * 获取Chart
     *
     * @param name
     * @param version
     * @return
     * @throws BaseAppException
     */
    public HelmChart getChart(String name, String version) throws BaseAppException {
        return helmClient.charts().chart(name, version);
    }

    /**
     * 获取Chart的values
     *
     * @param name
     * @param version
     * @return
     * @throws BaseAppException
     */
    public String getValues(String name, String version) throws BaseAppException {
        return helmClient.charts().values(name, version);
    }

    /**
     * 获取Chart的readme
     *
     * @param name
     * @param version
     * @return
     * @throws BaseAppException
     */
    public String getReadme(String name, String version) throws BaseAppException {
        return helmClient.charts().readme(name, version);
    }

    /**
     * 获取chart的定义
     *
     * @param name
     * @param version
     * @return
     */
    public HelmChartMetadata getMetadata(String name, String version) throws BaseAppException {
        return helmClient.charts().metadata(name, version);
    }

    /**
     * 获取chart的目录结构
     *
     * @param name
     * @param version
     * @param subdirectory chart子目录，为空表示chart根目录
     * @return
     */
    public List<ChartFile> getStructure(String name, String version, String subdirectory) throws BaseAppException {
        return helmClient.charts().structure(name, version, subdirectory);
    }

    /**
     * 获取Chart的文件
     *
     * @param name
     * @param version
     * @param filePath
     * @return
     */
    public String getFile(String name, String version, String filePath) throws BaseAppException {
        return helmClient.charts().file(name, version, filePath);
    }

    /**
     * 搜索Chart的文件
     *
     * @param name
     * @param version
     * @param keyword
     * @return
     * @throws BaseAppException
     */
    public List<ChartFile> searchFiles(String name, String version, String keyword) throws BaseAppException {
        return helmClient.charts().search(name, version, keyword);
    }

    /**
     * 获取Chart的Logo
     *
     * @param name
     * @param version
     * @return
     */
    public String getLogo(String name, String version) throws BaseAppException {
        HelmChartMetadata metadata = helmClient.charts().metadata(name, version);
        String logo = metadata.getIcon();
        if (StringUtils.startsWith(logo, "http")) {
            return logo;
        }
        // TODO: 是否存在本地文件？
        return "";
    }

    /**
     * 向仓库中推送chart
     *
     * @param tenantId
     * @param chartPath
     * @param repoName
     * @throws BaseAppException
     */
    public void push(Integer tenantId, String chartPath, String repoName) throws BaseAppException {
        helmClient.charts().push(chartPath, repoName);
    }

    /**
     * 拉取Chart
     *
     * @param name chart名称，含仓库名称
     * @param version chart版本
     * @return
     */
    public Path pullChart(String name, String version) throws BaseAppException {
        helmRepoService.update(getRepoName(name));
        helmClient.charts().pull(name, version);
        Path chartsDir = HelmClientUtil.chartsDownloadDir();
        String chartName = StringUtil.format("{}-{}.tgz", Splitter.on("/").splitToList(name).get(1), version);
        return Paths.get(chartsDir.toString(), FilenameUtils.getName(chartName));
    }

    /**
     * 从名称中获取仓库名
     *
     * @param name repoName/chartName
     * @return
     */
    private String getRepoName(String name) {
        return Splitter.on("/").splitToList(name).get(0);
    }
}
