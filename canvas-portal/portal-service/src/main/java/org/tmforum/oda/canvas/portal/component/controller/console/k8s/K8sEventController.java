package org.tmforum.oda.canvas.portal.component.controller.console.k8s;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.component.service.console.k8s.K8sEventService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.Event;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

/**
 * 提供Kubernetes Event管理相关接口
 *
 */
@RestController("kubernetes-event-controller")
@RequestMapping(value = "/console")
@Api(tags = "Kubernetes Event管理接口")
public class K8sEventController {
    @Autowired
    private K8sEventService k8sEventService;

    @GetMapping("/namespaces/{namespace}/events")
    @ApiOperation(value = "获取指定namespace下的Event列表")
    public ResponseEntity<List<Event>> listEvents(@PathVariable("namespace") String namespace,
                                                  @RequestParam(value = "involvedObjectName", required = false) String involvedObjectName) throws BaseAppException {
        List<Event> events = k8sEventService.listEvents(namespace, involvedObjectName);
        return ResponseEntity.ok(events);
    }

}
