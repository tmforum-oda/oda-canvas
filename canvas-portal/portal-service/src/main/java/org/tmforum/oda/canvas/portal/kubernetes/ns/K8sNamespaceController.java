package org.tmforum.oda.canvas.portal.kubernetes.ns;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

import io.fabric8.kubernetes.api.model.Namespace;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * Provides Kubernetes Namespaces API
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-namespace-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Namespace Management Interface")
public class K8sNamespaceController {
    private K8sNamespaceService k8sNamespaceService;

    public K8sNamespaceController(K8sNamespaceService k8sNamespaceService) {
        this.k8sNamespaceService = k8sNamespaceService;
    }

    @GetMapping("/namespaces")
    @ApiOperation(value = "Get the list of Namespaces")
    public ResponseEntity<List<Namespace>> listNamespaces(@ApiParam(value = "Namespace name, supports fuzzy matching") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException, BaseAppException {
        List<Namespace> namespaces = k8sNamespaceService.listNamespaces(keyword);
        return ResponseEntity.ok(namespaces);
    }

    @GetMapping("/namespaces/{name}")
    @ApiOperation(value = "Get the specified Namespace")
    public ResponseEntity<Namespace> getNamespace(@PathVariable("name") String name) throws BaseAppException {
        Namespace namespace = k8sNamespaceService.getNamespace(name);
        return ResponseEntity.ok(namespace);
    }

    @GetMapping("/namespaces/{name}/yaml")
    @ApiOperation(value = "Get the YAML of the specified Namespace")
    public ResponseEntity<YamlResult> getNamespaceAsYaml(@PathVariable("name") String name) throws BaseAppException {
        Namespace namespace = k8sNamespaceService.getNamespace(name);
        String yaml = Serialization.asYaml(namespace);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
