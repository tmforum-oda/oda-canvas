package org.tmforum.oda.canvas.portal.kubernetes.job;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

import io.fabric8.kubernetes.api.model.batch.v1.Job;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

@RestController("kubernetes-job-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Job Management Interface")
public class K8sJobController {
    private K8sJobService k8sJobService;

    public K8sJobController(K8sJobService k8sJobService) {
        this.k8sJobService = k8sJobService;
    }

    @GetMapping("/namespaces/{namespace}/jobs/{name}/yaml")
    @ApiOperation(value = "Get the YAML of the specified job")
    public ResponseEntity<YamlResult> getJobAsYaml(@PathVariable("namespace") String namespace,
                                                   @PathVariable("name") String name) throws BaseAppException {
        Job job = k8sJobService.getJob(namespace, name);
        String yaml = Serialization.asYaml(job);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
