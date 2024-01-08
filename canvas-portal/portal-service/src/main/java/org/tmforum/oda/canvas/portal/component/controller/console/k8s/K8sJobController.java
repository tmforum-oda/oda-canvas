package org.tmforum.oda.canvas.portal.component.controller.console.k8s;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sJobService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.batch.v1.Job;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;


@RestController("kubernetes-job-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Job管理接口")
public class K8sJobController {
    @Autowired
    private K8sJobService k8sJobService;

    @GetMapping("/namespaces/{namespace}/jobs/{name}/yaml")
    @ApiOperation(value = "获取指定的Pod的YAML")
    public ResponseEntity<YamlResult> getPodAsYaml(@PathVariable("namespace") String namespace,
                                                   @PathVariable("name") String name) throws BaseAppException {
        Job job = k8sJobService.getJob(namespace, name);
        String yaml = Serialization.asYaml(job);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
