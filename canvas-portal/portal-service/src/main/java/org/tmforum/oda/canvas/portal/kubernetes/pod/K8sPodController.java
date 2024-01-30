package org.tmforum.oda.canvas.portal.kubernetes.pod;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.infrastructure.MapRequestParam;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

import io.fabric8.kubernetes.api.model.Pod;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;


/**
 * Provides kubernetes pod api
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("kubernetes-pod-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Pod api")
public class K8sPodController {
    @Autowired
    private K8sPodService k8sPodService;

    @GetMapping("/namespaces/{namespace}/pods")
    @ApiOperation(value = "Retrieve the list of Pods in the specified namespace.")
    public ResponseEntity<List<Pod>> listPods(@PathVariable("namespace") String namespace,
                                              @MapRequestParam(value = "labels") Map<String, String> labels,
                                              @ApiParam(value = "Pod name, supports fuzzy matching.") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Pod> pods = k8sPodService.listPods(namespace, labels, keyword);
        return ResponseEntity.ok(pods);
    }

    @GetMapping("/namespaces/{namespace}/pods/{name}")
    @ApiOperation(value = "Retrieve the specified Pod")
    public ResponseEntity<Pod> getSecret(@PathVariable("namespace") String namespace,
                                         @PathVariable("name") String name) throws BaseAppException {
        Pod pod = k8sPodService.getPod(namespace, name);
        return ResponseEntity.ok(pod);
    }

    @GetMapping("/namespaces/{namespace}/pods/{name}/yaml")
    @ApiOperation(value = "Retrieve the YAML of the specified Pod")
    public ResponseEntity<YamlResult> getPodAsYaml(@PathVariable("namespace") String namespace,
                                                   @PathVariable("name") String name) throws BaseAppException {
        Pod pod = k8sPodService.getPod(namespace, name);
        String yaml = Serialization.asYaml(pod);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
