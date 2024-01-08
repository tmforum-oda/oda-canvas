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

import io.fabric8.kubernetes.api.model.networking.v1.Ingress;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

import org.tmforum.oda.canvas.portal.component.controller.console.dto.DeleteIngressResult;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sIngressService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

/**
 * 提供Kubernetes Ingress管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-ingress-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Ingress管理接口")
public class K8sIngressController {

    @Autowired
    private K8sIngressService k8sIngressService;

    @GetMapping("/namespaces/{namespace}/ingresses")
    @ApiOperation(value = "获取指定namespace下的Ingress列表")
    public ResponseEntity<List<Ingress>> listIngress(@PathVariable("namespace") String namespace, @ApiParam(value = "Deployment名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Ingress> ingresses = k8sIngressService.listIngress(namespace, keyword);
        return ResponseEntity.ok(ingresses);
    }

    @GetMapping("/namespaces/{namespace}/ingresses/{name}")
    @ApiOperation(value = "获取指定的Ingress")
    public ResponseEntity<Ingress> getIngress(@PathVariable("namespace") String namespace,
                                                    @PathVariable("name") String name) throws BaseAppException {
        Ingress ingress = k8sIngressService.getIngress(namespace, name);
        return ResponseEntity.ok(ingress);
    }

    @GetMapping("/namespaces/{namespace}/ingresses/{name}/yaml")
    @ApiOperation(value = "获取指定的Ingress的YAML")
    public ResponseEntity<YamlResult> getIngressAsYaml(@PathVariable("namespace") String namespace,
                                                          @PathVariable("name") String name) throws BaseAppException {
        Ingress ingress = k8sIngressService.getIngress(namespace, name);
        String yaml = Serialization.asYaml(ingress);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/ingresses/{name}")
    @ApiOperation(value = "删除ingress")
    public ResponseEntity<DeleteIngressResult> deleteIngress(@PathVariable("namespace") String namespace,
                                                             @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteIngressResult.builder().deleted(k8sIngressService.deleteIngress(namespace, name)).build());
    }
}
