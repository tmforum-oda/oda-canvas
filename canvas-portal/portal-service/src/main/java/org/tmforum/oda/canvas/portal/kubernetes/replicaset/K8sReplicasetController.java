package org.tmforum.oda.canvas.portal.kubernetes.replicaset;

import java.util.List;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.infrastructure.MapRequestParam;

import io.fabric8.kubernetes.api.model.apps.ReplicaSet;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

/**
 * Provides Kubernetes ReplicaSets API
 */
@RestController("kubernetes-replicaset-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Replicaset Management Interface")
public class K8sReplicasetController {
    private K8sReplicaSetService k8sReplicaSetService;

    public K8sReplicasetController(K8sReplicaSetService k8sReplicaSetService) {
        this.k8sReplicaSetService = k8sReplicaSetService;
    }

    @GetMapping("/namespaces/{namespace}/replicasets")
    @ApiOperation(value = "Retrieve the list of ReplicaSets under the specified namespace")
    public ResponseEntity<List<ReplicaSet>> listReplicaset(@PathVariable("namespace") String namespace,
                                                           @MapRequestParam(value = "labels") Map<String, String> labels) throws BaseAppException {
        List<ReplicaSet> replicaSets = k8sReplicaSetService.listReplicasets(namespace, labels);
        return ResponseEntity.ok(replicaSets);
    }

}
