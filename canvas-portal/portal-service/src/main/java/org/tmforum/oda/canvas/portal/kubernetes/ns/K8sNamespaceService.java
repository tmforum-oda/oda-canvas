package org.tmforum.oda.canvas.portal.kubernetes.ns;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.infrastructure.CanvasErrorCode;

import io.fabric8.kubernetes.api.model.Namespace;
import io.fabric8.kubernetes.client.KubernetesClient;

/**
 * Provides services related to Kubernetes Namespace resources
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sNamespaceService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sNamespaceService.class);

    private KubernetesClient kubeClient;

    public K8sNamespaceService(KubernetesClient kubeClient) {
        this.kubeClient = kubeClient;
    }

    /**
     * Retrieves a list of Namespaces
     *
     * @param keyword Supports filtering by keyword (name)
     */
    public List<Namespace> listNamespaces(String keyword) throws BaseAppException {
        try {
            List<Namespace> namespaces = kubeClient.namespaces().list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return namespaces;
            }
            return namespaces.stream().filter(namespace -> namespace.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list namespaces, error: ", e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_NAMESPACE_FAILED);
        }
        return Collections.emptyList();
    }

    /**
     * Retrieves a specified Namespace
     *
     * @param name The name of the Namespace
     * @return
     */
    public Namespace getNamespace(String name) throws BaseAppException {
        Namespace namespace = null;
        try {
            namespace = kubeClient.namespaces().withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_NAMESPACE_FAILED, name);
        }

        if (namespace == null) {
            ExceptionPublisher.publish(CanvasErrorCode.NAMESPACE_NOT_EXIST, name);
        }
        return namespace;
    }
}
