package org.tmforum.oda.canvas.portal.kubernetes.configmap;

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

import io.fabric8.kubernetes.api.model.ConfigMap;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * Provides Kubernetes ConfigMap API
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-configmap-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes ConfigMap API")
public class K8sConfigMapController {
    @Autowired
    private K8sConfigMapService k8sConfigMapService;

    @GetMapping("/namespaces/{namespace}/configmaps")
    @ApiOperation(value = "Get the list of ConfigMaps under the specified namespace")
    public ResponseEntity<List<ConfigMap>> listConfigMaps(@PathVariable("namespace") String namespace,
                                                          @ApiParam(value = "ConfigMap name, supports fuzzy matching") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<ConfigMap> configMaps = k8sConfigMapService.listConfigMaps(namespace, keyword);
        return ResponseEntity.ok(configMaps);
    }

    @GetMapping("/namespaces/{namespace}/configmaps/{name}")
    @ApiOperation(value = "Get the specified ConfigMap")
    public ResponseEntity<ConfigMap> getService(@PathVariable("namespace") String namespace,
                                                @PathVariable("name") String name) throws BaseAppException {
        ConfigMap configMap = k8sConfigMapService.getConfigMap(namespace, name);
        return ResponseEntity.ok(configMap);
    }

    @GetMapping("/namespaces/{namespace}/configmaps/{name}/yaml")
    @ApiOperation(value = "Get the YAML of the specified ConfigMap")
    public ResponseEntity<YamlResult> getServiceAsYaml(@PathVariable("namespace") String namespace,
                                                       @PathVariable("name") String name) throws BaseAppException {
        ConfigMap configMap = k8sConfigMapService.getConfigMap(namespace, name);
        String yaml = Serialization.asYaml(configMap);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/configmaps/{name}")
    @ApiOperation(value = "Delete the ConfigMap")
    public ResponseEntity<DeleteConfigMapResult> deleteDeployment(@PathVariable("namespace") String namespace,
                                                                  @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteConfigMapResult.builder().deleted(k8sConfigMapService.deleteConfigMap(namespace, name)).build());
    }
}