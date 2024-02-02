package org.tmforum.oda.canvas.portal.helm;

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
 * Provides Helm Chart related services
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
     * Get the list of Charts
     *
     * @param repoName The repository name, which needs to be a complete repository name
     * @param keyword  The keyword for the chart name
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> listCharts(String repoName, String keyword) throws BaseAppException {
        return helmClient.charts().list(repoName, keyword, false);
    }

    /**
     * Get the list of chart versions
     *
     * @param name The chart to query the version of, format: reponame/chartname
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> listVersions(String name) throws BaseAppException {
        return helmClient.charts().versions(name);
    }

    /**
     * Get the Chart
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
     * Get the values of the Chart
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
     * Get the readme of the Chart
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
     * Get the definition of the chart
     *
     * @param name
     * @param version
     * @return
     */
    public HelmChartMetadata getMetadata(String name, String version) throws BaseAppException {
        return helmClient.charts().metadata(name, version);
    }

    /**
     * Get the directory structure of the chart
     *
     * @param name
     * @param version
     * @param subdirectory The subdirectory of the chart, empty means the root directory of the chart
     * @return
     */
    public List<ChartFile> getStructure(String name, String version, String subdirectory) throws BaseAppException {
        return helmClient.charts().structure(name, version, subdirectory);
    }

    /**
     * Get the file of the Chart
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
     * Search for files in the Chart
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
     * Get the logo of the Chart
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
        // TODO: Check if there is a local file?
        return "";
    }

    /**
     * Push a chart to the repository
     *
     * @param chartPath
     * @param repoName
     * @throws BaseAppException
     */
    public void push(String chartPath, String repoName) throws BaseAppException {
        helmClient.charts().push(chartPath, repoName);
    }

    /**
     * Pull a Chart
     *
     * @param name    The name of the chart, including the repository name
     * @param version The version of the chart
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
     * Extract the repository name from the name
     *
     * @param name repoName/chartName
     * @return
     */
    private String getRepoName(String name) {
        return Splitter.on("/").splitToList(name).get(0);
    }
}
