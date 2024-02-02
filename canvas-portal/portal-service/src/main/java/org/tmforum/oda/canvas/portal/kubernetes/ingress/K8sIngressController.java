package org.tmforum.oda.canvas.portal.kubernetes.ingress;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

import io.fabric8.kubernetes.api.model.networking.v1.Ingress;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * Provides Kubernetes Ingress resources API
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-ingress-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Ingress Management Interface")
public class K8sIngressController {

    private K8sIngressService k8sIngressService;

    public K8sIngressController(K8sIngressService k8sIngressService) {
        this.k8sIngressService = k8sIngressService;
    }

    @GetMapping("/namespaces/{namespace}/ingresses")
    @ApiOperation(value = "Retrieve the list of Ingresses in the specified namespace")
    public ResponseEntity<List<Ingress>> listIngress(@PathVariable("namespace") String namespace, @ApiParam(value = "The name of the Deployment, supports fuzzy matching") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Ingress> ingresses = k8sIngressService.listIngress(namespace, keyword);
        return ResponseEntity.ok(ingresses);
    }

    @GetMapping("/namespaces/{namespace}/ingresses/{name}")
    @ApiOperation(value = "Get the specified Ingress")
    public ResponseEntity<Ingress> getIngress(@PathVariable("namespace") String namespace,
                                              @PathVariable("name") String name) throws BaseAppException {
        Ingress ingress = k8sIngressService.getIngress(namespace, name);
        return ResponseEntity.ok(ingress);
    }

    @GetMapping("/namespaces/{namespace}/ingresses/{name}/yaml")
    @ApiOperation(value = "Get the YAML of the specified Ingress")
    public ResponseEntity<YamlResult> getIngressAsYaml(@PathVariable("namespace") String namespace,
                                                       @PathVariable("name") String name) throws BaseAppException {
        Ingress ingress = k8sIngressService.getIngress(namespace, name);
        String yaml = Serialization.asYaml(ingress);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/ingresses/{name}")
    @ApiOperation(value = "Delete the specified Ingress")
    public ResponseEntity<DeleteIngressResult> deleteIngress(@PathVariable("namespace") String namespace,
                                                             @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteIngressResult.builder().deleted(k8sIngressService.deleteIngress(namespace, name)).build());
    }
}
