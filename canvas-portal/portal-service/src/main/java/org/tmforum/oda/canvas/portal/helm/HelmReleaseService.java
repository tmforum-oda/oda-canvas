package org.tmforum.oda.canvas.portal.helm;

import java.util.List;

import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmRelease;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmReleaseRevision;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmReleaseStatus;

import com.google.common.base.Splitter;

/**
 * Provides Helm Release related services
 *
 * @author li.peilong
 * @date 2022/12/09
 */
@Service
public class HelmReleaseService {

    private final HelmClient helmClient;

    public HelmReleaseService(HelmClient helmClient) {
        this.helmClient = helmClient;
    }

    /**
     * Get the list of releases under a namespace
     *
     * @param namespace The namespace
     * @param keyword   The keyword for release name
     * @return
     * @throws BaseAppException
     */
    public List<HelmRelease> listReleases(String namespace, String keyword) throws BaseAppException {
        return helmClient.releases().list(namespace, keyword, -1);
    }

    /**
     * Get a release
     *
     * @param namespace
     * @param releaseName
     * @return
     * @throws BaseAppException
     */
    public HelmRelease getRelease(String namespace, String releaseName) throws BaseAppException {
        return helmClient.releases().get(namespace, releaseName);
    }

    /**
     * Get detailed information of a Release
     *
     * @param namespace
     * @param releaseName
     * @return
     * @throws BaseAppException
     */
    public HelmReleaseDetail getReleaseDetail(String namespace, String releaseName) throws BaseAppException {
        HelmReleaseDetail result = new HelmReleaseDetail();
        HelmRelease release = helmClient.releases().get(namespace, releaseName);
        BeanUtils.copyProperties(release, result);
        HelmReleaseStatus status = helmClient.releases().status(namespace, releaseName);
        BeanUtils.copyProperties(status, result);
        HelmReleaseDescription description = HelmReleaseDescription.from(status.getDescription());
        BeanUtils.copyProperties(description, result);
        return result;
    }

    /**
     * Upgrade a Release
     *
     * @param release
     * @param upgradeHelmReleaseDto
     * @throws BaseAppException
     */
    public void upgradeRelease(String release, UpgradeHelmReleaseDto upgradeHelmReleaseDto) throws BaseAppException {
        List<String> parts = Splitter.on("/").limit(2).splitToList(upgradeHelmReleaseDto.getChart());
        HelmReleaseDescription description = HelmReleaseDescription.builder()
                .repoName(parts.get(0))
                .chartName(parts.get(1))
                .chartVersion(upgradeHelmReleaseDto.getVersion())
                .description(upgradeHelmReleaseDto.getDescription())
                .build();
        helmClient.releases()
                .upgrade(upgradeHelmReleaseDto.getNamespace(),
                        release, upgradeHelmReleaseDto.getChart(),
                        upgradeHelmReleaseDto.getVersion(),
                        description.toBase64String(),
                        upgradeHelmReleaseDto.getValues());
    }

    /**
     * Install a Release
     *
     * @param installHelmReleaseDto
     * @throws BaseAppException
     */
    public void installRelease(InstallHelmReleaseDto installHelmReleaseDto) throws BaseAppException {
        List<String> parts = Splitter.on("/").limit(2).splitToList(installHelmReleaseDto.getChart());
        HelmReleaseDescription description = HelmReleaseDescription.builder()
                .repoName(parts.get(0))
                .chartName(parts.get(1))
                .chartVersion(installHelmReleaseDto.getVersion())
                .description(installHelmReleaseDto.getDescription())
                .build();
        helmClient
                .releases()
                .install(installHelmReleaseDto.getNamespace(),
                        installHelmReleaseDto.getRelease(),
                        installHelmReleaseDto.getChart(),
                        installHelmReleaseDto.getVersion(),
                        description.toBase64String(),
                        installHelmReleaseDto.getValues());
    }

    /**
     * Rollback a Release
     *
     * @param tenantId
     * @param namespace
     * @param release
     * @param revision
     * @throws BaseAppException
     */
    public void rollbackRelease(Integer tenantId, String namespace, String release, Integer revision) throws BaseAppException {
        helmClient
                .releases()
                .rollback(namespace, release, revision);
    }

    /**
     * Uninstall a Release
     *
     * @param namespace
     * @param release
     * @throws BaseAppException
     */
    public void uninstallRelease(String namespace, String release) throws BaseAppException {
        helmClient.releases().uninstall(namespace, release);
    }

    /**
     * Get the historical versions of a Release
     *
     * @param namespace
     * @param release
     * @return
     * @throws BaseAppException
     */
    public List<HelmReleaseRevision> listHistoryRevisions(String namespace, String release) throws BaseAppException {
        List<HelmReleaseRevision> revisions = helmClient.releases().history(namespace, release);
        // Restore the description to its actual content
        revisions.forEach(helmReleaseRevision -> helmReleaseRevision.setDescription(HelmReleaseDescription.from(helmReleaseRevision.getDescription()).getDescription()));
        return revisions;
    }

    /**
     * Get the values of a release (full set)
     *
     * @param namespace
     * @param release
     * @param revision
     * @param all
     * @return
     * @throws BaseAppException
     */
    public String getValues(String namespace, String release, int revision, Boolean all) throws BaseAppException {
        return helmClient.releases().values(namespace, release, revision, all);
    }

    /**
     * Get the notes of a release
     *
     * @param namespace
     * @param release
     * @param revision
     * @return
     * @throws BaseAppException
     */
    public String getNotes(String namespace, String release, int revision) throws BaseAppException {
        return helmClient.releases().notes(namespace, release, revision);
    }
}
