package org.tmforum.oda.canvas.portal.kubernetes.deployment;

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

import io.fabric8.kubernetes.api.model.apps.Deployment;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * Provides Kubernetes Deployment API.
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-deployment-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Deployment Management Interface")
public class K8sDeploymentController {

    private K8sDeploymentService k8sDeploymentService;

    public K8sDeploymentController(K8sDeploymentService k8sDeploymentService) {
        this.k8sDeploymentService = k8sDeploymentService;
    }

    @GetMapping("/namespaces/{namespace}/deployments")
    @ApiOperation(value = "Get the list of Deployments in the specified namespace")
    public ResponseEntity<List<Deployment>> listDeployments(@PathVariable("namespace") String namespace,
                                                            @ApiParam(value = "Deployment name, supports fuzzy matching")
                                                            @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Deployment> deployments = k8sDeploymentService.listDeployments(namespace, keyword);
        return ResponseEntity.ok(deployments);
    }

    @GetMapping("/namespaces/{namespace}/deployments/{name}")
    @ApiOperation(value = "Get the specified Deployment")
    public ResponseEntity<Deployment> getDeployment(@PathVariable("namespace") String namespace,
                                                    @PathVariable("name") String name) throws BaseAppException {
        Deployment deployment = k8sDeploymentService.getDeployment(namespace, name);
        return ResponseEntity.ok(deployment);
    }

    @GetMapping("/namespaces/{namespace}/deployments/{name}/yaml")
    @ApiOperation(value = "Get the YAML of the specified Deployment")
    public ResponseEntity<YamlResult> getDeploymentAsYaml(@PathVariable("namespace") String namespace,
                                                          @PathVariable("name") String name) throws BaseAppException {
        Deployment deployment = k8sDeploymentService.getDeployment(namespace, name);
        String yaml = Serialization.asYaml(deployment);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/deployments/{name}")
    @ApiOperation(value = "Delete the Deployment")
    public ResponseEntity<DeleteDeployResult> deleteDeployment(@PathVariable("namespace") String namespace,
                                                               @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteDeployResult.builder().deleted(k8sDeploymentService.deleteDeployment(namespace, name)).build());
    }
}
