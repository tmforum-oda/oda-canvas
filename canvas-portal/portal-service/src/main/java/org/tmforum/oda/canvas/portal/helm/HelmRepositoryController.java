package org.tmforum.oda.canvas.portal.helm;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.helm.client.operation.repo.HelmRepo;

import com.google.common.collect.Maps;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * Provides Helm Repository API
 *
 * @author li.peilong
 * @date 2023/02/13
 */
@RestController("helm-repository-controller")
@RequestMapping(value = "/console/helm")
@Api(tags = "Helm Repository Management Interface")
public class HelmRepositoryController {
    private final HelmRepoService helmRepoService;

    public HelmRepositoryController(HelmRepoService helmRepoService) {
        this.helmRepoService = helmRepoService;
    }

    @PostMapping("/repositories/{name}/update")
    @ApiOperation(value = "Update repository")
    public ResponseEntity updateRepo(@ApiParam(value = "Repository name") @PathVariable("name") String name) throws BaseAppException {
        helmRepoService.update(name);
        return ResponseEntity.ok(Maps.newHashMap());
    }

    @GetMapping("/repositories")
    @ApiOperation(value = "Get list of repositories")
    public ResponseEntity<List<HelmRepo>> listRepos(@ApiParam(value = "Repository name keyword") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<HelmRepo> repos = helmRepoService.listRepos(keyword);
        return ResponseEntity.ok(repos);
    }
}
