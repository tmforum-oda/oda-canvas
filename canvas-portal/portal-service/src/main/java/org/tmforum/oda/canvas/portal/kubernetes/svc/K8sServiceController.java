package org.tmforum.oda.canvas.portal.kubernetes.svc;

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

import io.fabric8.kubernetes.api.model.Service;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

/**
 * Provides Kubernetes Services API
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-service-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Service Management Interfaces")
public class K8sServiceController {
    @Autowired
    private K8sServiceService k8sServiceService;

    @GetMapping("/namespaces/{namespace}/services")
    @ApiOperation(value = "Get the list of Services in the specified namespace")
    public ResponseEntity<List<Service>> listServices(@PathVariable("namespace") String namespace,
                                                      @ApiParam(value = "Service name, supports fuzzy matching") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Service> services = k8sServiceService.listServices(namespace, keyword);
        return ResponseEntity.ok(services);
    }

    @GetMapping("/namespaces/{namespace}/services/{name}")
    @ApiOperation(value = "Get the specified Service")
    public ResponseEntity<Service> getService(@PathVariable("namespace") String namespace,
                                              @PathVariable("name") String name) throws BaseAppException {
        Service service = k8sServiceService.getService(namespace, name);
        return ResponseEntity.ok(service);
    }

    @GetMapping("/namespaces/{namespace}/services/{name}/yaml")
    @ApiOperation(value = "Get the YAML of the specified Service")
    public ResponseEntity<YamlResult> getServiceAsYaml(@PathVariable("namespace") String namespace,
                                                       @PathVariable("name") String name) throws BaseAppException {
        Service service = k8sServiceService.getService(namespace, name);
        String yaml = Serialization.asYaml(service);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }

    @DeleteMapping("/namespaces/{namespace}/services/{name}")
    @ApiOperation(value = "Delete the specified service by name")
    public ResponseEntity<DeleteServiceResult> deleteService(@PathVariable("namespace") String namespace,
                                                             @PathVariable("name") String name) throws BaseAppException {
        return ResponseEntity.ok(DeleteServiceResult.builder().deleted(k8sServiceService.deleteService(namespace, name)).build());
    }
}