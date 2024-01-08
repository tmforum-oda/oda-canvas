package org.tmforum.oda.canvas.portal.component.controller.console.k8s;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.component.infrastructure.MapRequestParam;
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sReplicasetService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.apps.ReplicaSet;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;


/**
 * 提供Kubernetes Replicaset管理相关接口
 *
 */
@RestController("kubernetes-replicaset-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Event管理接口")
public class K8sReplicasetController {
    @Autowired
    private K8sReplicasetService k8sReplicasetService;

    @GetMapping("/namespaces/{namespace}/replicasets")
    @ApiOperation(value = "获取指定namespace下的Replicaset列表")
    public ResponseEntity<List<ReplicaSet>> listReplicaset(@PathVariable("namespace") String namespace,
                                                           @MapRequestParam(value = "labels") Map<String, String> labels) throws BaseAppException {
        List<ReplicaSet> replicaSets = k8sReplicasetService.listReplicasets(namespace, labels);
        return ResponseEntity.ok(replicaSets);
    }

}
