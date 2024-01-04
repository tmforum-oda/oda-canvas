package org.tmform.oda.canvas.portal.component.service.console.helm;

import com.google.common.base.Splitter;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmform.oda.canvas.portal.component.controller.console.dto.InstallHelmReleaseDto;
import org.tmform.oda.canvas.portal.component.controller.console.dto.UpgradeHelmReleaseDto;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmRelease;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmReleaseRevision;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmReleaseStatus;

import java.util.List;

/**
 * 提供Helm Release相关服务
 *
 * @author li.peilong
 * @date 2022/12/09
 */
@Service
public class HelmReleaseService {
    private static final Logger LOGGER = LoggerFactory.getLogger(HelmReleaseService.class);
    @Autowired
    private HelmClient helmClient;

    /**
     * 获取命名空间下的release列表
     *
     * @param namespace 命名空间
     * @param keyword release名称关键字
     * @return
     * @throws BaseAppException
     */
    public List<HelmRelease> listReleases(String namespace, String keyword) throws BaseAppException {
        return helmClient.releases().list(namespace, keyword, -1);
    }

    /**
     * 获取release
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
     * 获取Release的详细信息
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
     * 升级Release
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
     * 安装Release
     *
     * @param installHelmReleaseDto
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
     * 回滚Release
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
     * 卸载Release
     *
     * @param tenantId
     * @param namespace
     * @param release
     * @throws BaseAppException
     */
    public void uninstallRelease(Integer tenantId, String namespace, String release) throws BaseAppException {
        helmClient
                .releases()
                .uninstall(namespace, release);

        // 同步Deployment到应用
        //syncToApplication(namespace);
    }

    /**
     * 获取Release的历史版本
     *
     * @param namespace
     * @param release
     * @return
     */
    public List<HelmReleaseRevision> listHistoryRevisions(String namespace, String release) throws BaseAppException {
        List<HelmReleaseRevision> revisions = helmClient.releases().history(namespace, release);
        // 将description恢复成真实的
        revisions.forEach(helmReleaseRevision -> helmReleaseRevision.setDescription(HelmReleaseDescription.from(helmReleaseRevision.getDescription()).getDescription()));
        return revisions;
    }

    /**
     * 获取release的values(全量)
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
     * 获取release的notes
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
