package org.tmform.oda.canvas.portal.component.controller.console.helm;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmform.oda.canvas.portal.component.controller.console.dto.InstallHelmReleaseDto;
import org.tmform.oda.canvas.portal.component.controller.console.dto.UpgradeHelmReleaseDto;
import org.tmform.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmform.oda.canvas.portal.component.service.console.helm.HelmReleaseDetail;
import org.tmform.oda.canvas.portal.component.service.console.helm.HelmReleaseService;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmRelease;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmReleaseRevision;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import javax.validation.Valid;
import java.util.List;

/**
 * 提供Kubernetes Release管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("helm-release-controller")
@RequestMapping(value = "/console/helm")
@Api(tags = "Helm Release管理接口")
public class HelmReleaseController {
    @Autowired
    private HelmReleaseService helmReleaseService;

    @GetMapping("/releases")
    @ApiOperation(value = "获取Release列表")
    public ResponseEntity<List<HelmRelease>> listReleases(@RequestParam("namespace") String namespace,
                                                          @ApiParam(value = "release名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<HelmRelease> releases = helmReleaseService.listReleases(namespace, keyword);
        return ResponseEntity.ok(releases);
    }

    @GetMapping("/releases/{release}")
    @ApiOperation(value = "获取Release")
    public ResponseEntity<HelmRelease> getRelease(@PathVariable("release") String releaseName, @RequestParam("namespace") String namespace) throws BaseAppException {
        HelmRelease release = helmReleaseService.getRelease(namespace, releaseName);
        return ResponseEntity.ok(release);
    }

    @GetMapping("/releases/{release}/detail")
    @ApiOperation(value = "获取Release详细信息")
    public ResponseEntity<HelmReleaseDetail> getReleaseDetail(@RequestParam("namespace") String namespace,
                                                              @PathVariable("release") String releaseName) throws BaseAppException {
        HelmReleaseDetail releaseDetail = helmReleaseService.getReleaseDetail(namespace, releaseName);
        return ResponseEntity.ok(releaseDetail);
    }

    @PostMapping("/releases")
    @ApiOperation(value = "安装Release")
    public void installRelease(@RequestBody @Valid InstallHelmReleaseDto installHelmReleaseDto) throws BaseAppException {
        helmReleaseService.installRelease(installHelmReleaseDto);
    }
    @PostMapping("/releases/{release}/upgrade")
    @ApiOperation(value = "升级Release")
    public void upgradeRelease(@PathVariable("release") String release,
                               @RequestBody @Valid UpgradeHelmReleaseDto upgradeHelmReleaseDto) throws BaseAppException {
        helmReleaseService.upgradeRelease(release, upgradeHelmReleaseDto);
    }

    @PostMapping("/releases/{release}/revisions/{revision}/rollback")
    @ApiOperation(value = "回滚Release")
    public void rollbackRelease(@PathVariable("release") String release,
                                @PathVariable("revision") Integer revision,
                                @RequestParam("tenantId") Integer tenantId,
                                @RequestParam("namespace") String namespace) throws BaseAppException {
        helmReleaseService.rollbackRelease(tenantId, namespace, release, revision);
    }

    @DeleteMapping("/releases/{release}/uninstall")
    @ApiOperation(value = "卸载Release")
    public void uninstallRelease(@PathVariable("release") String release,
                                 @RequestParam("tenantId") Integer tenantId,
                                 @RequestParam("namespace") String namespace) throws BaseAppException {
        helmReleaseService.uninstallRelease(tenantId, namespace, release);
    }

    @GetMapping("/releases/{release}/revisions")
    @ApiOperation(value = "获取release的历史版本")
    public ResponseEntity<List<HelmReleaseRevision>> listHistoryRevisions(@PathVariable("release") String release,
                                                                          @RequestParam("namespace") String namespace) throws BaseAppException {
        List<HelmReleaseRevision> revisions = helmReleaseService.listHistoryRevisions(namespace, release);
        return ResponseEntity.ok(revisions);
    }

    @GetMapping("/releases/{release}/values")
    @ApiOperation(value = "获取release的values")
    public ResponseEntity<YamlResult> getValues(@PathVariable("release") String release,
                                                @RequestParam(value = "revision", required = false, defaultValue = "-1") Integer revision,
                                                @RequestParam(value = "all", required = false, defaultValue = "true") Boolean all,
                                                @RequestParam("namespace") String namespace) throws BaseAppException {
        String values = helmReleaseService.getValues(namespace, release, revision, all);
        return ResponseEntity.ok(YamlResult.builder().data(values).build());
    }

    @GetMapping("/releases/{release}/notes")
    @ApiOperation(value = "获取release的notes")
    public ResponseEntity<String> getNotes(@PathVariable("release") String release,
                                           @RequestParam(value = "revision", required = false, defaultValue = "-1") Integer revision,
                                           @RequestParam("namespace") String namespace) throws BaseAppException {
        String notes = helmReleaseService.getNotes(namespace, release, revision);
        return ResponseEntity.ok(notes);
    }
}
