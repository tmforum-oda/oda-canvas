package org.tmforum.oda.canvas.portal.component.service.console.k8s;

import java.util.Collections;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.component.infrastructure.CanvasErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;

import io.fabric8.kubernetes.api.model.apps.ReplicaSet;
import io.fabric8.kubernetes.client.KubernetesClient;


/**
 * 提供Kubernetes Replicaset资源相关服务
 */
@Service
public class K8sReplicasetService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sReplicasetService.class);

    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取Replicaset列表
     *
     * @param namespace namespace
     * @param labels label
     */
    public List<ReplicaSet> listReplicasets(String namespace, Map<String, String> labels) throws BaseAppException {
        try {
            return kubeClient.apps().replicaSets().inNamespace(namespace).withLabels(labels == null ? Collections.emptyMap() : labels).list().getItems();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list replicaset in namespace[{}], tenantId[{}], error: ", namespace);
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_REPLICASET_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    public ReplicaSet getReplicaSet(KubernetesClient kubeClient, String namespace, String replicaName) throws BaseAppException {
        try {
            return kubeClient.apps().replicaSets().inNamespace(namespace).withName(replicaName).get();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list replicaset in namespace[{}], error: ", namespace);
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_REPLICASET_FAILED, namespace);
        }
        return null;
    }

}
