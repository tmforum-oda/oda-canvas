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

import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sServiceService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.DeleteServiceResult;


import io.fabric8.kubernetes.api.model.Service;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * 提供Kubernetes Service管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-service-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Service管理接口")
public class K8sServiceController {
    @Autowired
    private K8sServiceService k8sServiceService;

    @GetMapping("/namespaces/{namespace}/services")
    @ApiOperation(value = "获取指定namespace下的Service列表")
    public ResponseEntity<List<Service>> listServices(@PathVariable("namespace") String namespace,
                                       @ApiParam(value = "服务名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Service> services = k8sServiceService.listServices(namespace, keyword);
        return ResponseEntity.ok(services);
    }

    @GetMapping("/namespaces/{namespace}/services/{name}")
    @ApiOperation(value = "获取指定的Service")
    public ResponseEntity<Service> getService(@PathVariable("namespace") String namespace,
                                              @PathVariable("name") String name) throws BaseAppException {
        Service service = k8sServiceService.getService(namespace, name);
        return ResponseEntity.ok(service);
    }

    @GetMapping("/namespaces/{namespace}/services/{name}/yaml")
    @ApiOperation(value = "获取指定的Service的YAML")
    public ResponseEntity<YamlResult> getServiceAsYaml(@PathVariable("namespace") String namespace,
                                                       @PathVariable("name") String name) throws BaseAppException {
        Service service = k8sServiceService.getService(namespace, name);
        String yaml = Serialization.asYaml(service);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/services/{name}")
    @ApiOperation(value = "删除指定名称的service")
    public ResponseEntity<DeleteServiceResult> deleteService(@PathVariable("namespace") String namespace,
                                                                @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteServiceResult.builder().deleted(k8sServiceService.deleteService(namespace, name)).build());
    }
}
