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
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sEndpointService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.Endpoints;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * @author liu.jiang
 * @date 2022/12/12
 * @time 13:51
 */
@RestController("kubernetes-endpoint-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Endpoint管理接口")
public class K8sEndpointController {
    @Autowired
    private K8sEndpointService k8sEndpointService;

    @GetMapping("/namespaces/{namespace}/endpoints")
    @ApiOperation(value = "获取指定namespace下的Service列表")
    public ResponseEntity<List<Endpoints>> listServices(@PathVariable("namespace") String namespace, @ApiParam(value = "服务名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Endpoints> endpoints = k8sEndpointService.listEndpoints(namespace, keyword);
        return ResponseEntity.ok(endpoints);
    }

    @GetMapping("/namespaces/{namespace}/endpoints/{name}")
    @ApiOperation(value = "获取指定的Service")
    public ResponseEntity<Endpoints> getService(@PathVariable("namespace") String namespace,
                                              @PathVariable("name") String name) throws BaseAppException {
        Endpoints endpoint = k8sEndpointService.getEndpoint(namespace, name);
        return ResponseEntity.ok(endpoint);
    }

    @GetMapping("/namespaces/{namespace}/endpoints/{name}/yaml")
    @ApiOperation(value = "获取指定的Service的YAML")
    public ResponseEntity<YamlResult> getServiceAsYaml(@PathVariable("namespace") String namespace,
                                                       @PathVariable("name") String name) throws BaseAppException {
        Endpoints endpoint = k8sEndpointService.getEndpoint(namespace, name);
        String yaml = Serialization.asYaml(endpoint);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
