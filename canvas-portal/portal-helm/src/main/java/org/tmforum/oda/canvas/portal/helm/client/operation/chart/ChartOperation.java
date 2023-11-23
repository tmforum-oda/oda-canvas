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
 * 提供Chart相关操作
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
    // TODO：暂时仅支持ChartMuseum
    private static final String PUSH_CHART_CMD = "helm cm-push {} {} --insecure";

    /**
     * 将Chart推送到仓库中
     *
     * @param chartPath
     * @param repoName
     */
    public void push(String chartPath, String repoName) throws BaseAppException {
        push(chartPath, repoName, 60);
    }

    /**
     * 将Chart推送到仓库中
     *
     * @param chartPath
     * @param repoName
     * @param timeout
     * @throws BaseAppException
     */
    public void push(String chartPath, String repoName, Integer timeout) throws BaseAppException {
        Preconditions.checkArgument(Files.exists(Paths.get(chartPath)), "chart path[%s] does not exist", chartPath);
        Preconditions.checkArgument(StringUtils.isNoneBlank(repoName), "repoName can not be null or empty");
        String cmd = StringUtil.format(PUSH_CHART_CMD, chartPath, repoName);
        if (timeout != null && timeout > 0) {
            cmd = cmd.concat(" --timeout ").concat(timeout.toString());
        }
        exec(cmd);
    }

    /**
     * 获取chart文件的内容
     *
     * @param name 格式repoName/chartName
     * @param version
     * @param filePath chart文件路径，相对于chart根目录
     * @return
     */
    public String file(String name, String version, String filePath) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(filePath), "filePath can not be null or empty");
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
     * 检索Chart中的文件
     *
     * @param name 格式repoName/chartName
     * @param version
     * @param keyword 文件的名字关键字
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
     * 将路径转换成ChartFile
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
     * 获取 Chart的目录结构
     *
     * @param name 格式repoName/chartName
     * @param version
     * @param subdirectory 子目录，不设置表示获取chart根路径结构
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
     * 下载chart
     *
     * @param name chart名称，格式repoName/chartName
     * @param version
     * @param update 下载前是否更新仓库
     * @param untar 是否解压chart
     * @throws BaseAppException
     */
    public void pull(String name, String version, Boolean update, Boolean untar) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name can not be null or empty, and format is: repoName/charName,for example:bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version can not be null or empty");

        Path chartsDir = HelmClientUtil.chartsDownloadDir();
        String chartName = StringUtil.format("{}-{}.tgz", Splitter.on("/").splitToList(name).get(1), version);
        Path chart = chartsDir.resolve(chartName);
        // 不存在则拉取
        if (!Files.exists(chart)) {
            // 先更新一下仓库
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
        // 进行解压
        Path destDir = HelmClientUtil.chartUntarDir(name, version);
        // 因为chart压缩包会包含一层chart名的目录，所以此处往上一层
        if (destDir.getParent() != null) {
            destDir = destDir.getParent();
        }
        // 已经解压
        if (Files.exists(destDir)) {
            return;
        }
        try {
            // 不使用--untar参数，该参数无法按照版本进行解压
            HelmClientUtil.tgzUncompress(chart.toFile(), destDir);
        }
        catch (Exception e) {
            // 异常清理目录
            FileUtils.deleteQuietly(destDir.toFile());
            ExceptionPublisher.publish(e);
        }

    }

    /**
     * 下载chart
     *
     * @param name 格式repoName/chartName
     * @param version
     * @throws BaseAppException
     */
    public void pull(String name, String version) throws BaseAppException {
        pull(name, version, false);
    }

    /**
     * 下载chart
     *
     * @param name 格式repoName/chartName
     * @param version
     * @param untar
     * @throws BaseAppException
     */
    public void pull(String name, String version, Boolean untar) throws BaseAppException {
        pull(name, version, false, untar);
    }

    /**
     * 获取Chart的完整定义
     *
     * @param name 格式repoName/chartName
     * @param version
     * @return
     * @throws BaseAppException
     */
    public HelmChartMetadata metadata(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name can not be null or empty, and format is: repoName/charName,for example:bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version can not be null or empty");
        String cmd = StringUtil.format(SHOW_CHART_CMD, name, version);
        String output = exec(cmd);
        Yaml yaml = new Yaml();
        HelmChartMetadata chartDefinition = yaml.loadAs(output, HelmChartMetadata.class);
        // 重置name
        chartDefinition.setName(name);
        return chartDefinition;
    }

    /**
     * 获取Chart的默认values配置
     *
     * @param name 格式repoName/chartName
     * @param version
     * @return YAML格式values
     * @throws BaseAppException
     */
    public String values(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name can not be null or empty, and format is: repoName/charName,for example:bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version can not be null or empty");
        String cmd = StringUtil.format(SHOW_CHART_VALUES_CMD, name, version);
        return exec(cmd);
    }

    /**
     * 显示chart的README文件的内容
     *
     * @param name 格式repoName/chartName
     * @param version
     * @return
     * @throws BaseAppException
     */
    public String readme(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name can not be null or empty, and format is: repoName/charName,for example:bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version can not be null or empty");
        String cmd = StringUtil.format(SHOW_CHART_README_CMD, name, version);
        return exec(cmd);
    }

    /**
     * 显示chart的CRD文件的内容
     *
     * @param name 格式repoName/chartName
     * @param version
     * @return
     * @throws BaseAppException
     */
    public String crds(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name can not be null or empty, and format is: repoName/charName,for example:bitnami/nginx");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "version can not be null or empty");
        String cmd = StringUtil.format(SHOW_CHART_CRDS_CMD, name, version);
        return exec(cmd);
    }

    /**
     * 获取chart
     *
     * @param name
     * @param version 未指定，返回最新版本
     * @return
     * @throws BaseAppException
     */
    public HelmChart chart(String name, String version) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name can not be null or empty, and format is: repoName/charName,for example:bitnami/nginx");
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
     * 获取chart列表
     *
     * @param keyword chart名称关键字
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> list(String keyword) throws BaseAppException {
        return list(null, keyword, false);
    }

    /**
     * 获取chart列表
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
     * 获取chart列表
     * @param repoName 仓库名称
     * @param keyword chart名称关键字
     * @param devel 是否显示开发版本
     * @param update 获取列表前是否更新仓库
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> list(String repoName, String keyword, Boolean devel, Boolean update) throws BaseAppException {
        // 先更新一下仓库
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
     * 获取某Chart的所有版本
     *
     * @param name chart名称，格式repoName/chartName
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> versions(String name) throws BaseAppException {
        return versions(name, false);
    }

    /**
     * 获取某Chart的所有版本
     *
     * @param name chart名称，格式repoName/chartName
     * @param devel
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> versions(String name, Boolean devel) throws BaseAppException {
        return versions(name, devel, false);
    }

    /**
     * 获取某Chart的所有版本
     *
     * @param name chart名称，格式repoName/chartName
     * @param devel 是否显示开发版本
     * @param update 获取版本前是否更新仓库
     * @return
     * @throws BaseAppException
     */
    public List<HelmChart> versions(String name, Boolean devel, Boolean update) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name) && name.contains("/"), "name can not be null or empty, and format is: repoName/charName,for example:bitnami/nginx");
        // 先更新下仓库
        if (BooleanUtils.isTrue(update)) {
            new RepoOperation().update(getRepoName(name));
        }
        String cmd = StringUtil.format(LIST_CHART_VERSION_CMD, name);
        if (BooleanUtils.isTrue(devel)) {
            cmd = cmd.concat(" --devel");
        }
        String output = exec(cmd);
        List<HelmChart> result = JsonUtil.json2List(output, HelmChart.class);
        // 需要精确匹配名称
        return result.stream().filter(chart -> StringUtils.equals(name, chart.getName())).collect(Collectors.toList());
    }
}
