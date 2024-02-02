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

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Provides helm release operations
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
     * Get the notes of a release
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
     * Get the notes of a specific revision of a release
     *
     * @param namespace
     * @param release
     * @param revision If less than 0, get the configuration of the latest revision
     * @return notes
     * @throws BaseAppException
     */
    public String notes(String namespace, String release, Integer revision) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
        String cmd = StringUtil.format(GET_RELEASE_NOTES_CMD, release, namespace);
        if (revision != null && revision > 0) {
            cmd = cmd.concat(" --revision ").concat(String.valueOf(revision));
        }
        String output = exec(cmd);
        return output;
    }

    /**
     * Get the status of a release
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
     * Get the status of a release
     *
     * @param namespace
     * @param release
     * @param revision If less than or equal to 0, query the current revision
     * @return
     * @throws BaseAppException
     */
    public HelmReleaseStatus status(String namespace, String release, Integer revision) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
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
     * Get the manifest of a release
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
     * Get the manifest of a specific revision of a release
     *
     * @param namespace
     * @param release
     * @param revision If less than 0, get the configuration of the latest revision
     * @return manifest
     * @throws BaseAppException
     */
    public String manifest(String namespace, String release, Integer revision) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
        String cmd = StringUtil.format(GET_RELEASE_MANIFEST_CMD, release, namespace);
        if (revision != null && revision > 0) {
            cmd = cmd.concat(" --revision ").concat(String.valueOf(revision));
        }
        String output = exec(cmd);
        return output;
    }

    /**
     * Get the configuration of a release
     *
     * @param namespace
     * @param release
     * @return yaml format of the full configuration
     * @throws BaseAppException
     */
    public String values(String namespace, String release) throws BaseAppException {
        return values(namespace, release, -1, true);
    }

    /**
     * Get the configuration of a specific revision of a release
     *
     * @param namespace
     * @param release
     * @param revision If less than 0, get the configuration of the latest revision
     * @param all Whether to display all values, false only displays user-defined configurations
     * @return yaml format of the full configuration
     * @throws BaseAppException
     */
    public String values(String namespace, String release, Integer revision, boolean all) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
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
     * Install a release
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
     * Install a release
     *
     * @param namespace
     * @param release
     * @param chart
     * @param version
     * @param description
     * @param values
     * @param update Whether to update the repository before installation
     * @throws BaseAppException
     */
    public void install(String namespace, String release, String chart, String version, String description, String values, Boolean update) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(chart), "chart cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "release version cannot be null or empty");
        String cmd = StringUtil.format(INSTALL_RELEASE_CMD, release, chart, version, namespace);

        // Update the repository first
        if (BooleanUtils.isTrue(update)) {
            new RepoOperation().update(getRepoName(chart));
        }

        if (StringUtils.isNoneBlank(description)) {
            cmd = cmd.concat(" --description \"").concat(description).concat("\"");
        }
        if (StringUtils.isNoneBlank(values)) {
            // Write values to a file first
            String path = writeToFile(values, "yaml");
            cmd = cmd.concat(" --values \"").concat(path).concat("\"");
        }
        exec(cmd);
    }

    /**
     * Upgrade a release
     *
     * @param namespace
     * @param release
     * @param chart The chart to upgrade, in the format repo/chart, e.g., bitnami/nginx
     * @param version
     * @param description
     * @param values
     * @throws BaseAppException
     */
    public void upgrade(String namespace, String release, String chart, String version, String description, String values) throws BaseAppException {
        upgrade(namespace, release, chart, version, description, values, false);
    }
    /**
     * Upgrade a release
     *
     * @param namespace
     * @param release
     * @param chart The chart to upgrade, in the format repo/chart, e.g., bitnami/nginx
     * @param version
     * @param description
     * @param update Whether to update the repository before upgrading
     * @throws BaseAppException
     */
    public void upgrade(String namespace, String release, String chart, String version, String description, String values, Boolean update) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(chart), "chart cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(version), "release version cannot be null or empty");
        // Update the repository first
        if (BooleanUtils.isTrue(update)) {
            new RepoOperation().update(getRepoName(chart));
        }
        String cmd = StringUtil.format(UPGRADE_RELEASE_CMD, release, chart, version, namespace);
        if (StringUtils.isNoneBlank(description)) {
            cmd = cmd.concat(" --description \"").concat(description).concat("\"");
        }
        if (StringUtils.isNoneBlank(values)) {
            // Write values to a file first
            String path = writeToFile(values, "yaml");
            cmd = cmd.concat(" --values \"").concat(path).concat("\"");
        }
        exec(cmd);
    }

    /**
     * Uninstall a release
     *
     * @param namespace
     * @param release
     * @throws BaseAppException
     */
    public void uninstall(String namespace, String release) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
        String cmd = StringUtil.format(UNINSTALL_RELEASE_CMD, release, namespace);
        exec(cmd);
    }

    /**
     * Rollback a release
     *
     * @param namespace
     * @param release
     * @param revision
     * @throws BaseAppException
     */
    public void rollback(String namespace, String release, Integer revision) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
        Preconditions.checkArgument(revision != null && revision > 0, "revision must be greater than 0");
        String cmd = StringUtil.format(ROLLBACK_RELEASE_CMD, release, revision, namespace);
        exec(cmd);
    }

    /**
     * Get the history of release versions
     *
     * @param namespace Namespace
     * @param release Release name
     * @return
     * @throws BaseAppException
     */
    public List<HelmReleaseRevision> history(String namespace, String release) throws BaseAppException {
        return history(namespace, release, -1);
    }
    /**
     * Get the history of release versions
     *
     * @param namespace Namespace
     * @param release Release name
     * @param limit The maximum number of release history versions to return
     * @return
     * @throws BaseAppException
     */
    public List<HelmReleaseRevision> history(String namespace, String release, Integer limit) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(namespace), "namespace cannot be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(release), "release name cannot be null or empty");
        String cmd = StringUtil.format(LIST_RELEASE_HISTORY_CMD, release, namespace);
        if (limit != null && limit > 0) {
            cmd = cmd.concat(" --max").concat(String.valueOf(limit));
        }
        String output = exec(cmd);
        List<HelmReleaseRevision> result = JsonUtil.json2List(output, HelmReleaseRevision.class);
        result.forEach(helmReleaseRevision -> {
            helmReleaseRevision.setReleaseName(release);
            helmReleaseRevision.setNamespace(namespace);
        });
        return result;
    }

    /**
     * Get the list of releases
     *
     * @param namespace Namespace
     * @return
     * @throws BaseAppException
     */
    public List<HelmRelease> list(String namespace) throws BaseAppException {
        return list(namespace, null, -1);
    }

    /**
     * Get a release
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
     * Get the list of releases
     *
     * @param namespace Namespace, if not specified, query all namespaces
     * @param keyword Release name keyword
     * @param limit The maximum number of releases to return
     * @param statuses Get releases of specified statuses deployed/failed/uninstalling/pending/superseded/uninstalling
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
        // Get releases of specified statuses
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
        else {
            // Service Account file
            File saTokenPathFile = new File("/var/run/secrets/kubernetes.io/serviceaccount/token");
            try {
                String serviceTokenCandidate = new String(Files.readAllBytes(saTokenPathFile.toPath()));
                cmd = cmd.concat(" --kube-token ").concat(serviceTokenCandidate);
            }
            catch (IOException e) {
                ExceptionPublisher.publish(HelmClientExceptionErrorCode.HELM_RELEASE_NOT_EXIST);
            }
        }
        if (StringUtils.isNoneBlank(this.helmClientConfig.getKubeContext())) {
            cmd = cmd.concat(" --kube-context ").concat(this.helmClientConfig.getKubeContext());
        }
        if (StringUtils.isNoneBlank(this.helmClientConfig.getKubeApiserver())) {
            cmd = cmd.concat(" --kube-apiserver ").concat(this.helmClientConfig.getKubeApiserver());
        }
        else {
            String kubernetesServiceHost = System.getenv("KUBERNETES_SERVICE_HOST");
            String kubernetesServicePort = System.getenv("KUBERNETES_SERVICE_PORT");
            cmd = cmd.concat(" --kube-apiserver ").concat("https://" + joinHostPort(kubernetesServiceHost, kubernetesServicePort));
        }
        return super.exec(cmd);
    }

    private static String joinHostPort(String host, String port) {
        if (host.indexOf(':') >= 0) {
            // Host is an IPv6
            return "[" + host + "]:" + port;
        }
        return host + ":" + port;
    }
}
