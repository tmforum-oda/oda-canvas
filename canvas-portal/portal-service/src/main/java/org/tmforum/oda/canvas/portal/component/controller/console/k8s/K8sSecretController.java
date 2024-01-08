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
import org.tmforum.oda.canvas.portal.component.controller.console.dto.DeleteSecretResult;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sSecretService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.Secret;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * 提供Kubernetes Secret管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-secret-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Secret管理接口")
public class K8sSecretController {
    @Autowired
    private K8sSecretService k8sSecretService;

    @GetMapping("/namespaces/{namespace}/secrets")
    @ApiOperation(value = "获取指定namespace下的Secret列表")
    public ResponseEntity<List<Secret>> listSecrets(@PathVariable("namespace") String namespace,
                                                       @ApiParam(value = "Secret名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Secret> secrets = k8sSecretService.listSecrets(namespace, keyword);
        return ResponseEntity.ok(secrets);
    }

    @GetMapping("/namespaces/{namespace}/secrets/{name}")
    @ApiOperation(value = "获取指定的Secret")
    public ResponseEntity<Secret> getSecret(@PathVariable("namespace") String namespace,
                                            @PathVariable("name") String name) throws BaseAppException {
        Secret secret = k8sSecretService.getSecret(namespace, name);
        return ResponseEntity.ok(secret);
    }

    @GetMapping("/namespaces/{namespace}/secrets/{name}/yaml")
    @ApiOperation(value = "获取指定的Secret的YAML")
    public ResponseEntity<YamlResult> getSecretAsYaml(@PathVariable("namespace") String namespace,
                                                      @PathVariable("name") String name) throws BaseAppException {
        Secret secret = k8sSecretService.getSecret(namespace, name);
        String yaml = Serialization.asYaml(secret);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/secrets/{name}")
    @ApiOperation(value = "删除secret")
    public ResponseEntity<DeleteSecretResult> deleteSecret(@PathVariable("namespace") String namespace,
                                                           @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteSecretResult.builder().deleted(k8sSecretService.deleteSecret(namespace, name)).build());
    }
}
