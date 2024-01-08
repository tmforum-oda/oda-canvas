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
import org.tmforum.oda.canvas.portal.component.controller.console.dto.DeleteConfigMapResult;
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sConfigMapService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.YamlResult;

import io.fabric8.kubernetes.api.model.ConfigMap;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * 提供Kubernetes ConfigMap管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-configmap-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes ConfigMap管理接口")
public class K8sConfigMapController {
    @Autowired
    private K8sConfigMapService k8sConfigMapService;

    @GetMapping("/namespaces/{namespace}/configmaps")
    @ApiOperation(value = "获取指定namespace下的ConfigMap列表")
    public ResponseEntity<List<ConfigMap>> listConfigMaps(@PathVariable("namespace") String namespace,
                                                          @ApiParam(value = "ConfigMap名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<ConfigMap> configMaps = k8sConfigMapService.listConfigMaps(namespace, keyword);
        return ResponseEntity.ok(configMaps);
    }

    @GetMapping("/namespaces/{namespace}/configmaps/{name}")
    @ApiOperation(value = "获取指定的ConfigMap")
    public ResponseEntity<ConfigMap> getService(@PathVariable("namespace") String namespace,
                                                @PathVariable("name") String name) throws BaseAppException {
        ConfigMap configMap = k8sConfigMapService.getConfigMap(namespace, name);
        return ResponseEntity.ok(configMap);
    }

    @GetMapping("/namespaces/{namespace}/configmaps/{name}/yaml")
    @ApiOperation(value = "获取指定的ConfigMap的YAML")
    public ResponseEntity<YamlResult> getServiceAsYaml(@PathVariable("namespace") String namespace,
                                                       @PathVariable("name") String name) throws BaseAppException {
        ConfigMap configMap = k8sConfigMapService.getConfigMap(namespace, name);
        String yaml = Serialization.asYaml(configMap);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/configmaps/{name}")
    @ApiOperation(value = "删除configmap")
    public ResponseEntity<DeleteConfigMapResult> deleteDeployment(@PathVariable("namespace") String namespace,
                                                                  @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteConfigMapResult.builder().deleted(k8sConfigMapService.deleteConfigMap(namespace, name)).build());
    }
}

