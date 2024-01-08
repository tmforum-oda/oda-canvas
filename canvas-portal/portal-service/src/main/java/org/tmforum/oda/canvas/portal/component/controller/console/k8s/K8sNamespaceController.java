package org.tmforum.oda.canvas.portal.component.controller.console.k8s;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sNamespaceService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.Namespace;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;


/**
 * 提供Kubernetes Namespace管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-namespace-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Namespace管理接口")
public class K8sNamespaceController {
    @Autowired
    private K8sNamespaceService k8sNamespaceService;

    @GetMapping("/namespaces")
    @ApiOperation(value = "获取Namespace列表")
    public ResponseEntity<List<Namespace>> listNamespaces(@ApiParam(value = "Namespace名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException, BaseAppException {
        List<Namespace> namespaces = k8sNamespaceService.listNamespaces(keyword);
        return ResponseEntity.ok(namespaces);
    }

    @GetMapping("/namespaces/{name}")
    @ApiOperation(value = "获取指定的Namespace")
    public ResponseEntity<Namespace> getNamespace(@PathVariable("name") String name) throws BaseAppException {
        Namespace namespace = k8sNamespaceService.getNamespace(name);
        return ResponseEntity.ok(namespace);
    }

    @GetMapping("/namespaces/{name}/yaml")
    @ApiOperation(value = "获取指定的Namespace的YAML")
    public ResponseEntity<YamlResult> getNamespaceAsYaml(@PathVariable("name") String name) throws BaseAppException {
        Namespace namespace = k8sNamespaceService.getNamespace(name);
        String yaml = Serialization.asYaml(namespace);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
