package org.tmforum.oda.canvas.portal.component.controller.console.k8s;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.DeleteDeployResult;
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sDeploymentService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.apps.Deployment;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * 提供Kubernetes Deployment管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-deployment-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Deployment管理接口")
public class K8sDeploymentController {
    @Autowired
    private K8sDeploymentService k8sDeploymentService;

    @GetMapping("/namespaces/{namespace}/deployments")
    @ApiOperation(value = "获取指定namespace下的Deployment列表")
    public ResponseEntity<List<Deployment>> listDeployments(@PathVariable("namespace") String namespace, @ApiParam(value = "Deployment名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Deployment> deployments = k8sDeploymentService.listDeployments(namespace, keyword);
        return ResponseEntity.ok(deployments);
    }

    @GetMapping("/namespaces/{namespace}/deployments/{name}")
    @ApiOperation(value = "获取指定的Deployment")
    public ResponseEntity<Deployment> getDeployment(@PathVariable("namespace") String namespace,
                                                    @PathVariable("name") String name) throws BaseAppException {
        Deployment deployment = k8sDeploymentService.getDeployment(namespace, name);
        return ResponseEntity.ok(deployment);
    }

    @GetMapping("/namespaces/{namespace}/deployments/{name}/yaml")
    @ApiOperation(value = "获取指定的Deployment的YAML")
    public ResponseEntity<YamlResult> getDeploymentAsYaml(@PathVariable("namespace") String namespace,
                                                          @PathVariable("name") String name) throws BaseAppException {
        Deployment deployment = k8sDeploymentService.getDeployment(namespace, name);
        String yaml = Serialization.asYaml(deployment);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/deployments/{name}")
    @ApiOperation(value = "删除deploy")
    public ResponseEntity<DeleteDeployResult> deleteDeployment(@PathVariable("namespace") String namespace,
                                                               @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteDeployResult.builder().deleted(k8sDeploymentService.deleteDeployment(namespace, name)).build());
    }
}
