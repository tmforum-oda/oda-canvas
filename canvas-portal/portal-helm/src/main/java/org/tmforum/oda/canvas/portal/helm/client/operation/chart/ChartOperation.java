package org.tmforum.oda.canvas.portal.helm.client.operation.chart;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.List;
import java.util.Optional;
import java.util.function.BiPredicate;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.BooleanUtils;
import org.apache.commons.lang3.StringUtils;
import org.yaml.snakeyaml.Yaml;

import com.google.common.base.Joiner;
import com.google.common.base.Preconditions;
import com.google.common.base.Splitter;
import com.google.common.collect.Lists;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.core.util.JsonUtil;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;
import org.tmforum.oda.canvas.portal.helm.client.HelmClientExceptionErrorCode;
import org.tmforum.oda.canvas.portal.helm.client.HelmClientUtil;
import org.tmforum.oda.canvas.portal.helm.client.operation.BaseOperation;
import org.tmforum.oda.canvas.portal.helm.client.operation.repo.RepoOperation;

/**
 * Provides Chart related operations
 *
 * @author li.peilong
 * @date 2022/12/08
 */
public class ChartOperation extends BaseOperation {
    private static final String LIST_CHART_CMD = "helm search repo {} -o json";
    private static final String LIST_CHART_VERSION_CMD = "helm search repo {} -l -o json";
    private static final String SHOW_CHART_VALUES_CMD = "helm show values {} --version {} --insecure-skip-tls-verify";
    private static final String SHOW_CHART_README_CMD = "helm show readme {} --version {} --insecure-skip-tls-verify";
    private static final String SHOW_CHART_CRDS_CMD = "helm show crds {} --version {} --insecure-skip-tls-verify";
    private static final String SHOW_CHART_CMD = "helm show chart {} --version {} --insecure-skip-tls-verify";
    private static final String PULL_CHART_CMD = "helm pull {} --version {} -d {} --insecure-skip-tls-verify";
    // TODO: Currently only supports ChartMuseum
    private static final String PUSH_CHART_CMD = "helm cm-push {} {} --insecure";

    /**
     * Pushes a Chart to the repository
     *
     * @param chartPath chartPath
     * @param repoName chart repo name
     */
    public void push(String chartPath, String repoName) throws BaseAppException {
        push(chartPath, repoName, 60);
    }

    /**
     * Pushes a Chart to the repository
     *
     * @param chartPath
     * @param repoName
     * @param timeout
     * @throws BaseAppException
     */
    public void push(String chartPath, String repoName, Integer timeout) throws BaseAppException {
        Preconditions.checkArgument(Files.exists(Paths.get(chartPath)), "chart path[%s] does not exist", chartPath);
        Preconditions.checkArgument(StringUtils.isNoneBlank(repoName), "repoName cannot be null or empty");
        String cmd = StringUtil.format(PUSH_CHART_CMD, chartPath, repoName);
        if (timeout != null && timeout > 0) {
            cmd = cmd.concat(" --timeout ").concat(timeout.toString());
        }
        exec(cmd);
    }

    /**
     * Gets the content of a chart file
     *
     * @param name Format repoName/chartName
     * @param version
     * @param filePath chart file path, relative to the chart root directory
     * @return
     */
    public String file(String name, String version, String filePath) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(filePath), "filePath cannot be null or empty");
        pull(name, version, true);
        Path chartDir = HelmClientUtil.chartUntarDir(name, version);
        Path path  = chartDir.resolve(filePath);
        try {
            String data = FileUtils.readFileToString(path.toFile(), StandardCharsets.UTF_8);
            // FIXME
            return null;
            // return SecurityUtil.base64Encrypt(data);
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, HelmClientExceptionErrorCode.HELM_GET_CHART_FILE_FAILED, name, version, filePath);
        }
        return "";
    }

    /**
     * Searches for files in a Chart
     *
     * @param name Format repoName/chartName
     * @param version
     * @param keyword file name keyword
     * @return
     * @throws BaseAppException
     */
    public List<ChartFile> search(String name, String version, String keyword) throws BaseAppException {
        pull(name, version, true);
        try {
            Stream<Path> pathStream = Files.find(HelmClientUtil.chartUntarDir(name, version), 100, new BiPredicate<Path, BasicFileAttributes>() {
                @Override
                public boolean test(Path path, BasicFileAttributes basicFileAttributes) {
                    if (basicFileAttributes.isDirectory()) {
                        return false;
                    }
                    if (StringUtils.isBlank(keyword) || StringUtils.contains(path.toFile().getName(), keyword)) {
                        return true;
                    }
                    return false;
                }
            });
            return toChartFiles(pathStream, HelmClientUtil.chartUntarDir(name, version));
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, HelmClientExceptionErrorCode.HELM_SEARCH_CHART_FILE_FAILED, name, version, keyword);
        }
        return Lists.newArrayList();
    }

    /**
     * Converts paths to ChartFile
     *
     * @param pathStream
     * @param chartDir
     * @return
     */
    private List<ChartFile> toChartFiles(Stream<Path> pathStream, Path chartDir) {
        if (pathStream == null || chartDir == null) {
            return Lists.newArrayList();
        }
        int startIndex = chartDir.toFile().getAbsolutePath().length() + 1;
        return pathStream.map(path -> {
            return ChartFile.builder()
                    .name(path.toFile().getName())
                    .directory(path.toFile().isDirectory())
                    .size(path.toFile().length())
                    .path(path.toFile().getAbsolutePath().substring(startIndex))
                    .build();
        }).collect(Collectors.toList());
    }
    /**
     * Gets the directory structure of a Chart
     *
     * @param name Format repoName/chartName
     * @param version
     * @param subdirectory subdirectory, not set means getting the root path structure of the chart
     * @return
     * @throws BaseAppException
     */
    public List<ChartFile> structure(String name, String version, String subdirectory) throws BaseAppException {
        pull(name, version, true);
        Path chartDir = HelmClientUtil.chartUntarDir(name, version);
        if (StringUtils.isNoneBlank(subdirectory)) {
            chartDir = chartDir.resolve(subdirectory);
        }
        try {
            Stream<Path> pathStream = Files.list(chartDir);
            return toChartFiles(pathStream, HelmClientUtil.chartUntarDir(name, version));
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, HelmClientExceptionErrorCode.HELM_GET_CHART_STRUCTURE_FAILED, name, version);
        }
        return Lists.newArrayList();

    }

    /**
     * Downloads a chart
     *
     * @param name chart name, format repoName/chartName
     * @param version
     * @param update whether to update the repository before downloading
     * @param untar whether to unzip the chart
     * @throws BaseAppException
     */
    public void pull(String name, String version, Boolean update, Boolean untar) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name cannot be null or empty, and format is: repoName/charName, for example: bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version cannot be null or empty");

        Path chartsDir = HelmClientUtil.chartsDownloadDir();
        String chartName = StringUtil.format("{}-{}.tgz", Splitter.on("/").splitToList(name).get(1), version);
        Path chart = chartsDir.resolve(chartName);
        // Pull if it doesn't exist
        if (!Files.exists(chart)) {
            // Update the repository first
            if (BooleanUtils.isTrue(update)) {
                new RepoOperation().update(getRepoName(name));
            }
            HelmClientUtil.createDirectories(chartsDir);
            String cmd = StringUtil.format(PULL_CHART_CMD, name, version, chartsDir.toFile().getAbsolutePath());
            exec(cmd);
        }

        if (!untar) {
            return;
        }
        // Unzip
        Path destDir = HelmClientUtil.chartUntarDir(name, version);
        // Since the chart package includes a directory named after the chart, move up one level here
        if (destDir.getParent() != null) {
            destDir = destDir.getParent();
        }
        // Skip if already unzipped
        if (Files.exists(destDir)) {
            return;
        }
        try {
            // Use uncompression instead of --untar parameter, as it does not decompress by version
            HelmClientUtil.tgzUncompress(chart.toFile(), destDir);
        }
        catch (Exception e) {
            // Clean up the directory on exception
            FileUtils.deleteQuietly(destDir.toFile());
            ExceptionPublisher.publish(e);
        }

    }

    /**
     * Downloads a chart
     *
     * @param name Format repoName/chartName
     * @param version
     * @throws BaseAppException
     */
    public void pull(String name, String version) throws BaseAppException {
        pull(name, version, false);
    }

    /**
     * Downloads a chart
     *
     * @param name Format repoName/chartName
     * @param version
     * @param untar
     * @throws BaseAppException
     */
    public void pull(String name, String version, Boolean untar) throws BaseAppException {
        pull(name, version, false, untar);
    }

    /**
     * Gets the full definition of a Chart
     *
     * @param name Format repoName/chartName
     * @param version
     * @return
     * @throws BaseAppException
     */
    public HelmChartMetadata metadata(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name cannot be null or empty, and format is: repoName/charName, for example: bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version cannot be null or empty");
        String cmd = StringUtil.format(SHOW_CHART_CMD, name, version);
        String output = exec(cmd);
        Yaml yaml = new Yaml();
        HelmChartMetadata chartDefinition = yaml.loadAs(output, HelmChartMetadata.class);
        // Reset name
        chartDefinition.setName(name);
        return chartDefinition;
    }

    /**
     * Gets the default values configuration of a Chart
     *
     * @param name Format repoName/chartName
     * @param version
     * @return YAML format values
     * @throws BaseAppException
     */
    public String values(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name cannot be null or empty, and format is: repoName/charName, for example: bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version cannot be null or empty");
        String cmd = StringUtil.format(SHOW_CHART_VALUES_CMD, name, version);
        return exec(cmd);
    }

    /**
     * Shows the content of the README file of a chart
     *
     * @param name Format repoName/chartName
     * @param version
     * @return
     * @throws BaseAppException
     */
    public String readme(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name cannot be null or empty, and format is: repoName/charName, for example: bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version cannot be null or empty");
        String cmd = StringUtil.format(SHOW_CHART_README_CMD, name, version);
        return exec(cmd);
    }

    /**
     * Shows the content of the CRD files of a chart
     *
     * @param name Format repoName/chartName
     * @param version
     * @return
     * @throws BaseAppException
     */
    public String crds(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name cannot be null or empty, and format is: repoName/charName, for example: bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version cannot be null or empty");
        String cmd = StringUtil.format(SHOW_CHART_CRDS_CMD, name, version);
        return exec(cmd);
    }

    /**
     * Gets a chart
     *
     * @param name
     * @param version If not specified, returns the latest version
     * @return
     * @throws BaseAppException
     */
    public HelmChart chart(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name cannot be null or empty, and format is: repoName/charName, for example: bitnami/nginx");
        List<HelmChart> charts = versions(name);
        if (CollectionUtils.isEmpty(charts)) {
            ExceptionPublisher.publish(HelmClientExceptionErrorCode.HELM_CHART_NOT_EXIST, name, version);
            return new HelmChart();
        }
        if (StringUtils.isBlank(version)) {
            return charts.get(0);
        }
        Optional<HelmChart> chart = charts.stream().filter(helmChart -> StringUtils.equals(helmChart.getVersion(), version)).findFirst();
        if (chart.isPresent()) {
            return chart.get();
        }
        ExceptionPublisher.publish(HelmClientExceptionErrorCode.HELM_CHART_NOT_EXIST, name, version);
        return new HelmChart();
    }

    /**
     * Gets a list of charts
     *
     * @param keyword chart name keyword
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> list(String keyword) throws BaseAppException {
        return list(null, keyword, false);
    }

    /**
     * Gets a list of charts
     *
     * @param repoName
     * @param keyword
     * @param devel
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> list(String repoName, String keyword, Boolean devel) throws BaseAppException {
        return list(repoName, keyword, devel, false);
    }

    /**
     * Gets a list of charts
     * @param repoName Repository name
     * @param keyword chart name keyword
     * @param devel whether to show development versions
     * @param update whether to update the repository before getting the list
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> list(String repoName, String keyword, Boolean devel, Boolean update) throws BaseAppException {
        // Update the repository first
        if (BooleanUtils.isTrue(update)) {
            new RepoOperation().update(repoName);
        }

        keyword = StringUtils.isNoneBlank(keyword) ? keyword : "";
        if (StringUtils.isNoneBlank(repoName)) {
            keyword = Joiner.on("/").join(repoName, keyword);
        }
        String cmd = StringUtil.format(LIST_CHART_CMD, keyword);
        if (BooleanUtils.isTrue(devel)) {
            cmd = cmd.concat(" --devel");
        }
        String output = exec(cmd);
        return JsonUtil.json2List(output, HelmChart.class);
    }

    /**
     * Gets all versions of a Chart
     *
     * @param name chart name, format repoName/chartName
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> versions(String name) throws BaseAppException {
        return versions(name, false);
    }

    /**
     * Gets all versions of a Chart
     *
     * @param name chart name, format repoName/chartName
     * @param devel
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> versions(String name, Boolean devel) throws BaseAppException {
        return versions(name, devel, false);
    }

    /**
     * Gets all versions of a Chart
     *
     * @param name chart name, format repoName/chartName
     * @param devel whether to show development versions
     * @param update whether to update the repository before getting versions
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> versions(String name, Boolean devel, Boolean update) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name cannot be null or empty, and format is: repoName/charName, for example: bitnami/nginx");
        // Update the repository first
        if (BooleanUtils.isTrue(update)) {
            new RepoOperation().update(getRepoName(name));
        }
        String cmd = StringUtil.format(LIST_CHART_VERSION_CMD, name);
        if (BooleanUtils.isTrue(devel)) {
            cmd = cmd.concat(" --devel");
        }
        String output = exec(cmd);
        List<HelmChart> result = JsonUtil.json2List(output, HelmChart.class);
        // Need to precisely match the name
        return result.stream().filter(chart -> StringUtils.equals(name, chart.getName())).collect(Collectors.toList());
    }
}
