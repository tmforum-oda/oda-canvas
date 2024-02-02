package org.tmforum.oda.canvas.portal.helm.client;

import org.tmforum.oda.canvas.portal.helm.client.operation.chart.ChartOperation;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.ReleaseOperation;
import org.tmforum.oda.canvas.portal.helm.client.operation.repo.RepoOperation;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;
import org.tmforum.oda.canvas.portal.helm.client.operation.InfoOperation;

import lombok.AllArgsConstructor;
import lombok.Builder;

import org.apache.commons.io.IOUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.InputStream;
import java.nio.file.Path;
import java.util.Objects;

/**
 * Helm client
 *
 * @author li.peilong
 * @date 2022/12/08
 * @see "https://github.com/helm/helm/releases"
 * @see "https://github.com/chartmuseum/helm-push/releases"
 */
@Builder
@AllArgsConstructor
public class HelmClient {
    private static final Logger LOGGER = LoggerFactory.getLogger(HelmClient.class);
    private static final String HELM_PACKAGE_NAME = "helm-v3.11.1-linux-amd64";
    private static final String HELM_PUSH_PACKAGE_NAME = "helm-push_0.10.3_linux_amd64";
    private HelmClientConfig helmClientConfig;

    /**
     * Operations related to Charts
     *
     * @return
     */
    public ChartOperation charts() {
        return new ChartOperation();
    }

    /**
     * Operations related to Chart repositories
     *
     * @return
     */
    public RepoOperation repos() {
        return new RepoOperation();
    }

    /**
     * Operations related to helm
     *
     * @return
     */
    public InfoOperation info() {
        return new InfoOperation();
    }

    /**
     * Operations related to Releases
     *
     * @return
     */
    public ReleaseOperation releases() {
        return new ReleaseOperation(this.helmClientConfig);
    }

    /**
     * Get the helm client configuration
     *
     * @return
     */
    public HelmClientConfig config() {
        return helmClientConfig;
    }

    // Install the helm client locally
    static {
        if (!HelmClientUtil.isWindows()) {
            InputStream in = null;
            // Install helm
            try {
                in = Objects.requireNonNull(HelmClient.class.getResourceAsStream(StringUtil.format("/install-package/{}.tar.gz", HELM_PACKAGE_NAME)), "Helm Client does not exist");
                HelmClientUtil.tgzUncompress(in, HelmClientUtil.workingDir(), true);
                // Set execution permissions
                File helmClientFile = new File(HelmClientUtil.workingDir().toFile().getAbsolutePath(), "helm");
                helmClientFile.setExecutable(true);
            } catch (Exception e) {
                LOGGER.error("Failed to install helm client, error: ", e);
            } finally {
                IOUtils.closeQuietly(in);
            }
            // Install helm push plugin
            try {
                in = Objects.requireNonNull(HelmClient.class.getResourceAsStream(StringUtil.format("/install-package/{}.tar.gz", HELM_PUSH_PACKAGE_NAME)), "Helm push plugin does not exist");
                Path pushPluginPath = HelmClientUtil.pluginDir().resolve("helm-push");
                HelmClientUtil.tgzUncompress(in, pushPluginPath);
                // Set execution permissions
                File helmClientFile = new File(pushPluginPath.resolve("bin").toFile().getAbsolutePath(), "helm-cm-push");
                helmClientFile.setExecutable(true);

            } catch (Exception e) {
                LOGGER.error("Failed to install helm push plugin, error: ", e);
            } finally {
                IOUtils.closeQuietly(in);
            }
        }
    }
}
