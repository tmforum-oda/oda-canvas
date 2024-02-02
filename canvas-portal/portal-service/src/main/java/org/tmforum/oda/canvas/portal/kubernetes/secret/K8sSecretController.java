package org.tmforum.oda.canvas.portal.kubernetes.secret;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

import io.fabric8.kubernetes.api.model.Secret;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * Provides Kubernetes Secret API
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-secret-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Secret Management Interface")
public class K8sSecretController {
    @Autowired
    private K8sSecretService k8sSecretService;

    @GetMapping("/namespaces/{namespace}/secrets")
    @ApiOperation(value = "Get the list of Secrets in the specified namespace")
    public ResponseEntity<List<Secret>> listSecrets(@PathVariable("namespace") String namespace,
                                                    @ApiParam(value = "Secret name, supports fuzzy matching") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Secret> secrets = k8sSecretService.listSecrets(namespace, keyword);
        return ResponseEntity.ok(secrets);
    }

    @GetMapping("/namespaces/{namespace}/secrets/{name}")
    @ApiOperation(value = "Get the specified Secret")
    public ResponseEntity<Secret> getSecret(@PathVariable("namespace") String namespace,
                                            @PathVariable("name") String name) throws BaseAppException {
        Secret secret = k8sSecretService.getSecret(namespace, name);
        return ResponseEntity.ok(secret);
    }

    @GetMapping("/namespaces/{namespace}/secrets/{name}/yaml")
    @ApiOperation(value = "Get the YAML of the specified Secret")
    public ResponseEntity<YamlResult> getSecretAsYaml(@PathVariable("namespace") String namespace,
                                                      @PathVariable("name") String name) throws BaseAppException {
        Secret secret = k8sSecretService.getSecret(namespace, name);
        String yaml = Serialization.asYaml(secret);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/secrets/{name}")
    @ApiOperation(value = "Delete the secret")
    public ResponseEntity<DeleteSecretResult> deleteSecret(@PathVariable("namespace") String namespace,
                                                           @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteSecretResult.builder().deleted(k8sSecretService.deleteSecret(namespace, name)).build());
    }
}
