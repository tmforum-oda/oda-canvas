package org.tmforum.oda.canvas.portal.helm.client.operation.release;

import com.google.common.base.Preconditions;
import org.tmforum.oda.canvas.portal.helm.client.operation.repo.RepoOperation;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.core.util.JsonPathUtil;
import org.tmforum.oda.canvas.portal.core.util.JsonUtil;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;

import org.tmforum.oda.canvas.portal.helm.client.HelmClientConfig;
import org.tmforum.oda.canvas.portal.helm.client.HelmClientExceptionErrorCode;
import org.tmforum.oda.canvas.portal.helm.client.operation.BaseOperation;

import org.apache.commons.lang3.BooleanUtils;
import org.apache.commons.lang3.StringUtils;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * 提供release相关操作
 *
 * @author li.peilong
 * @date 2022/12/07
 */
public class ReleaseOperation extends BaseOperation {
    private static final String LIST_RELEASE_CMD = "helm list -d --time-format \"2006-01-02 15:04:05\" --deployed --failed --pending --superseded --uninstalled --uninstalling  -o json";
    private static final String LIST_RELEASE_HISTORY_CMD = "helm history {} -n {} -o json";
    private static final String UPGRADE_RELEASE_CMD = "helm upgrade {} {} --version {} -n {}";
    private static final String ROLLBACK_RELEASE_CMD = "helm rollback {} {} -n {}";
    private static final String UNINSTALL_RELEASE_CMD = "helm uninstall {} -n {}";
    private static final String INSTALL_RELEASE_CMD = "helm install {} {} --version {} -n {} --insecure-skip-tls-verify";
    private static final String GET_RELEASE_VALUES_CMD = "helm get values {} -n {} -o yaml";
    private static final String GET_RELEASE_MANIFEST_CMD = "helm get manifest {} -n {}";
    private static final String GET_RELEASE_NOTES_CMD = "helm get notes {} -n {}";
    private static final String GET_RELEASE_STATUS_CMD = "helm status {} -n {} -o json";
    private HelmClientConfig helmClientConfig;
    public ReleaseOperation(HelmClientConfig helmClientConfig) {
        this.helmClientConfig = helmClientConfig;
    }

    /**
     * 获取release的notes
     *
     * @param namespace
     * @param release
     * @return
     * @throws BaseAppException
     */
    public String notes(String namespace, String release) throws BaseAppException {
        return notes(namespace, release, -1);
    }

    /**
     * 获取release指定revision的notes
     *
     * @param namespace
     * @param release
     * @param revision 小于0，获取最新revision的配置
     * @return notes
     * @throws BaseAppException
     */
    public String notes(String namespace, String release, Integer revision) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        String cmd = StringUtil.format(GET_RELEASE_NOTES_CMD, release, namespace);
        if (revision != null && revision > 0) {
            cmd = cmd.concat(" --revision ").concat(String.valueOf(revision));
        }
        String output = exec(cmd);
        return output;
    }

    /**
     * 获取Release的状态
     *
     * @param namespace
     * @param release
     * @return
     * @throws BaseAppException
     */
    public HelmReleaseStatus status(String namespace, String release) throws BaseAppException {
        return status(namespace, release, -1);
    }

    /**
     * 获取Release的状态
     *
     * @param namespace
     * @param release
     * @param revision 小于等于0，查询当前revision
     * @return
     * @throws BaseAppException
     */
    public HelmReleaseStatus status(String namespace, String release, Integer revision) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        String cmd = StringUtil.format(GET_RELEASE_STATUS_CMD, release, namespace);
        if (revision != null && revision > 0) {
            cmd = cmd.concat(" --revision ").concat(String.valueOf(revision));
        }
        String output = exec(cmd);
        HelmReleaseStatus status = JsonPathUtil.find(output, "$.info", HelmReleaseStatus.class);
        status.setName(release);
        status.setNamespace(namespace);
        return status;
    }

    /**
     * 获取release的manifest
     *
     * @param namespace
     * @param release
     * @return
     * @throws BaseAppException
     */
    public String manifest(String namespace, String release) throws BaseAppException {
        return manifest(namespace, release, -1);
    }

    /**
     * 获取release指定revision的manifest
     *
     * @param namespace
     * @param release
     * @param revision 小于0，获取最新revision的配置
     * @return manifest
     * @throws BaseAppException
     */
    public String manifest(String namespace, String release, Integer revision) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        String cmd = StringUtil.format(GET_RELEASE_MANIFEST_CMD, release, namespace);
        if (revision != null && revision > 0) {
            cmd = cmd.concat(" --revision ").concat(String.valueOf(revision));
        }
        String output = exec(cmd);
        return output;
    }

    /**
     * 获取release的配置
     *
     * @param namespace
     * @param release
     * @return yaml格式的全量配置
     * @throws BaseAppException
     */
    public String values(String namespace, String release) throws BaseAppException {
        return values(namespace, release, -1, true);
    }

    /**
     * 获取release指定revision的配置
     *
     * @param namespace
     * @param release
     * @param revision 小于0，获取最新revision的配置
     * @param all 是否显示所有的values， false仅显示用户自定义的配置
     * @return yaml格式的全量配置
     * @throws BaseAppException
     */
    public String values(String namespace, String release, Integer revision, boolean all) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        String cmd = StringUtil.format(GET_RELEASE_VALUES_CMD, release, namespace);
        if (revision != null && revision > 0) {
            cmd = cmd.concat(" --revision ").concat(String.valueOf(revision));
        }
        if (BooleanUtils.isNotFalse(all)) {
            cmd = cmd.concat(" --all ");
        }
        String output = exec(cmd);
        return output;
    }

    /**
     * 安装release
     *
     * @param namespace
     * @param release
     * @param chart
     * @param version
     * @param description
     * @param values
     * @throws BaseAppException
     */
    public void install(String namespace, String release, String chart, String version, String description, String values) throws BaseAppException {
        install(namespace, release, chart, version, description, values, false);
    }

    /**
     * 安装release
     *
     * @param namespace
     * @param release
     * @param chart
     * @param version
     * @param description
     * @param values
     * @throws BaseAppException
     */
    public void install(String namespace, String release, String chart, String version, String description, String values, Boolean update) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(chart), "chart can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "release version can not be null or empty");
        String cmd = StringUtil.format(INSTALL_RELEASE_CMD, release, chart, version, namespace);

        // 先更新一下仓库
        if (BooleanUtils.isTrue(update)) {
            new RepoOperation().update(getRepoName(chart));
        }

        if (StringUtils.isNoneBlank(description)) {
            cmd = cmd.concat(" --description \"").concat(description).concat("\"");
        }
        if (StringUtils.isNoneBlank(values)) {
            // 先将values写入文件
            String path = writeToFile(values, "yaml");
            cmd = cmd.concat(" --values \"").concat(path).concat("\"");
        }
        exec(cmd);
    }

    /**
     * 升级release
     *
     * @param namespace
     * @param release
     * @param chart 格式repo/chart,比如：bitnami/nginx
     * @param version
     * @param description
     * @param values
     * @throws BaseAppException
     */
    public void upgrade(String namespace, String release, String chart, String version, String description, String values) throws BaseAppException {
        upgrade(namespace, release, chart, version, description, values, false);
    }
    /**
     * 升级release
     *
     * @param namespace
     * @param release
     * @param chart 要升级的chart，格式repo/chart,比如：bitnami/nginx
     * @param version
     * @param description
     * @param update 升级前是否更新仓库
     * @throws BaseAppException
     */
    public void upgrade(String namespace, String release, String chart, String version, String description, String values, Boolean update) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(chart), "chart can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "release version can not be null or empty");
        // 先更新一下仓库
        if (BooleanUtils.isTrue(update)) {
            new RepoOperation().update(getRepoName(chart));
        }
        String cmd = StringUtil.format(UPGRADE_RELEASE_CMD, release, chart, version, namespace);
        if (StringUtils.isNoneBlank(description)) {
            cmd = cmd.concat(" --description \"").concat(description).concat("\"");
        }
        if (StringUtils.isNoneBlank(values)) {
            // 先将values写入文件
            String path = writeToFile(values, "yaml");
            cmd = cmd.concat(" --values \"").concat(path).concat("\"");
        }
        exec(cmd);
    }

    /**
     * 卸载release
     *
     * @param namespace
     * @param release
     * @throws BaseAppException
     */
    public void uninstall(String namespace, String release) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        String cmd = StringUtil.format(UNINSTALL_RELEASE_CMD, release, namespace);
        exec(cmd);
    }

    /**
     *
     * @param namespace
     * @param release
     * @param revision
     * @throws BaseAppException
     */
    public void rollback(String namespace, String release, Integer revision) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        Preconditions.checkArgument(revision != null && revision > 0, "revision must be greater than 0");
        String cmd = StringUtil.format(ROLLBACK_RELEASE_CMD, release, revision, namespace);
        exec(cmd);
    }

    /**
     * 获取release的历史版本列表
     *
     * @param namespace 命名空间
     * @param release release名称
     * @return
     * @throws BaseAppException
     */
    public List<HelmReleaseRevision> history(String namespace, String release) throws BaseAppException {
        return history(namespace, release, -1);
    }
    /**
     * 获取release的历史版本列表
     *
     * @param namespace 命名空间
     * @param release release名称
     * @param limit 返回的最大release历史版本数
     * @return
     * @throws BaseAppException
     */
    public List<HelmReleaseRevision> history(String namespace, String release, Integer limit) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name can not be null or empty");
        String cmd = StringUtil.format(LIST_RELEASE_HISTORY_CMD, release, namespace);
        if (limit != null && limit > 0) {
            cmd = cmd.concat(" --max").concat(String.valueOf(limit));
        }
        String output = exec(cmd);
        List<HelmReleaseRevision> result = JsonUtil.json2List(output, HelmReleaseRevision.class);
        result.stream().forEach(helmReleaseRevision -> {
            helmReleaseRevision.setReleaseName(release);
            helmReleaseRevision.setNamespace(namespace);
        });
        return result;
    }

    /**
     * 获取release列表
     *
     * @param namespace 命名空间
     * @return
     * @throws BaseAppException
     */
    public List<HelmRelease> list(String namespace) throws BaseAppException {
        return list(namespace, null, -1);
    }

    /**
     * 获取release
     *
     * @param namespace
     * @param releaseName
     * @return
     * @throws BaseAppException
     */
    public HelmRelease get(String namespace, String releaseName) throws BaseAppException {
        List<HelmRelease> releases = list(namespace, releaseName, -1);
        Optional<HelmRelease> release = releases.stream().filter(helmRelease -> StringUtils.equals(helmRelease.getName(), releaseName)).findAny();
        if (release.isPresent()) {
            return release.get();
        }
        ExceptionPublisher.publish(HelmClientExceptionErrorCode.HELM_RELEASE_NOT_EXIST, releaseName, namespace);
        return new HelmRelease();
    }

    /**
     * 获取release列表
     *
     * @param namespace 命名空间, 未指定则查询所有命名空间
     * @param keyword release名称关键字
     * @param limit 返回的最大release数
     * @param statuses 获取指定状态的release deployed/failed/uninstalling/pending/superseded/uninstalling
     * @return
     * @throws BaseAppException
     */
    public List<HelmRelease> list(String namespace, String keyword, Integer limit, String... statuses) throws BaseAppException {
        String cmd = LIST_RELEASE_CMD;
        if (StringUtils.isNoneBlank(namespace)) {
            cmd = cmd.concat(" -n ").concat(namespace);
        }
        else {
            cmd = cmd.concat(" -A");
        }
        if (StringUtils.isNoneBlank(keyword)) {
            cmd = cmd.concat(" -f \"").concat(keyword).concat("\"");
        }
        if (limit != null && limit > 0) {
            cmd = cmd.concat(" -m ").concat(String.valueOf(limit));
        }
        String output = exec(cmd);

        List<HelmRelease> result = JsonUtil.json2List(output, HelmRelease.class);
        if (statuses == null || statuses.length == 0) {
            return result;
        }
        // 获取指定状态的release
        return result.stream().filter(helmRelease -> Arrays.asList(statuses).contains(helmRelease.getStatus())).collect(Collectors.toList());
    }

    @Override
    protected String exec(String cmd) throws BaseAppException {
        if (this.helmClientConfig == null) {
            return super.exec(cmd);
        }
        if (BooleanUtils.isNotFalse(helmClientConfig.getKubeInsecureSkipTlsVerify())) {
            cmd = cmd.concat(" --kube-insecure-skip-tls-verify");
        }
        if (StringUtils.isNoneBlank(this.helmClientConfig.getKubeConfig())) {
            cmd = cmd.concat(" --kubeconfig ").concat(this.helmClientConfig.getKubeConfig());
        }
        if (StringUtils.isNoneBlank(this.helmClientConfig.getKubeContext())) {
            cmd = cmd.concat(" --kube-context ").concat(this.helmClientConfig.getKubeContext());
        }
        if (StringUtils.isNoneBlank(this.helmClientConfig.getKubeApiserver())) {
            cmd = cmd.concat(" --kube-apiserver ").concat(this.helmClientConfig.getKubeApiserver());
        }
        return super.exec(cmd);
    }
}
