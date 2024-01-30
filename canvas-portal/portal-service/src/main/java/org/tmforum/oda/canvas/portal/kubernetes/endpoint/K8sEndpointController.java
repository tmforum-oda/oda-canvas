package org.tmforum.oda.canvas.portal.kubernetes.endpoint;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

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
@Api(tags = "Kubernetes Endpoint Management Interface")
public class K8sEndpointController {
    private K8sEndpointService k8sEndpointService;

    public K8sEndpointController(K8sEndpointService k8sEndpointService) {
        this.k8sEndpointService = k8sEndpointService;
    }

    @GetMapping("/namespaces/{namespace}/endpoints")
    @ApiOperation(value = "Get the list of Endpoints under the specified namespace")
    public ResponseEntity<List<Endpoints>> listEndpoints(@PathVariable("namespace") String namespace, @ApiParam(value = "Service name, supports fuzzy matching") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Endpoints> endpoints = k8sEndpointService.listEndpoints(namespace, keyword);
        return ResponseEntity.ok(endpoints);
    }

    @GetMapping("/namespaces/{namespace}/endpoints/{name}")
    @ApiOperation(value = "Get the specified Endpoints")
    public ResponseEntity<Endpoints> getEndpoints(@PathVariable("namespace") String namespace,
                                                @PathVariable("name") String name) throws BaseAppException {
        Endpoints endpoint = k8sEndpointService.getEndpoint(namespace, name);
        return ResponseEntity.ok(endpoint);
    }

    @GetMapping("/namespaces/{namespace}/endpoints/{name}/yaml")
    @ApiOperation(value = "Get the YAML of the specified Service")
    public ResponseEntity<YamlResult> getEndpointsAsYaml(@PathVariable("namespace") String namespace,
                                                       @PathVariable("name") String name) throws BaseAppException {
        Endpoints endpoint = k8sEndpointService.getEndpoint(namespace, name);
        String yaml = Serialization.asYaml(endpoint);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
