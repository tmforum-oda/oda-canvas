package org.tmforum.oda.canvas.portal.kubernetes.event;

import java.util.Collections;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.infrastructure.CanvasErrorCode;

import io.fabric8.kubernetes.api.model.Event;
import io.fabric8.kubernetes.client.KubernetesClient;

/**
 * 提供Kubernetes Event资源相关服务
 */
@Service
public class K8sEventService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sEventService.class);

    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取Event列表
     *
     * @param namespace          namespace
     * @param involvedObjectName 对象名称
     */
    public List<Event> listEvents(String namespace, String involvedObjectName) throws BaseAppException {
        try {
            if (involvedObjectName != null) {
                return kubeClient.v1().events().inNamespace(namespace).withField("involvedObject.name", involvedObjectName).list().getItems();
            }
            else {
                return kubeClient.v1().events().inNamespace(namespace).list().getItems();
            }
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list pods in namespace[{}], error: ", namespace);
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_EVENT_FAILED, namespace);
        }
        return Collections.emptyList();
    }

}
