package io.oda.canvas.component.controller.console.helm;

import com.google.common.collect.Maps;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmform.oda.canvas.portal.component.service.console.helm.HelmRepoService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.helm.client.operation.repo.HelmRepo;

import java.util.List;

/**
 * 提供Helm Repository管理相关接口
 *
 * @author li.peilong
 * @date 2023/02/13
 */
@RestController("helm-repository-controller")
@RequestMapping(value = "/console/helm")
@Api(tags = "Helm Repository管理接口")
public class HelmRepositoryController {
    @Autowired
    private HelmRepoService helmRepoService;

    @PostMapping("/repositories/{name}/update")
    @ApiOperation(value = "更新仓库")
    public ResponseEntity updateRepo(@ApiParam(value = "仓库名称") @PathVariable("name") String name) throws BaseAppException {
        helmRepoService.update(name);
        return ResponseEntity.ok(Maps.newHashMap());
    }

    @GetMapping("/repositories")
    @ApiOperation(value = "获取仓库列表")
    public ResponseEntity<List<HelmRepo>> listRepos(@ApiParam(value = "仓库名称关键字") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<HelmRepo> repos = helmRepoService.listRepos(keyword);
        return ResponseEntity.ok(repos);
    }
}
