package org.tmforum.oda.canvas.portal.kubernetes.svc;

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
import org.tmforum.oda.canvas.portal.infrastructure.K8sResourceUtils;

import io.fabric8.kubernetes.client.KubernetesClient;


/**
 * Service for Kubernetes Service
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sServiceService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sServiceService.class);

    private KubernetesClient kubeClient;

    public K8sServiceService(KubernetesClient kubeClient) {
        this.kubeClient = kubeClient;
    }

    /**
     * Get a list of Services
     *
     * @param namespace namespace
     * @param keyword   Supports filtering by keyword (name)
     */
    public List<io.fabric8.kubernetes.api.model.Service> listServices(String namespace, String keyword) throws BaseAppException {
        try {
            List<io.fabric8.kubernetes.api.model.Service> services = kubeClient.services().inNamespace(namespace).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return services;
            }
            return services.stream().filter(service -> service.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list services in namespace[{}], error: ", namespace, e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_SERVICE_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * Get the specified Service
     *
     * @param namespace namespace
     * @param name      Service name
     * @return
     */
    public io.fabric8.kubernetes.api.model.Service getService(String namespace, String name) throws BaseAppException {
        io.fabric8.kubernetes.api.model.Service service = null;
        try {
            service = kubeClient.services().inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_SERVICE_FAILED, name, namespace);
        }

        if (service == null) {
            ExceptionPublisher.publish(CanvasErrorCode.SERVICE_NOT_EXIST, name, namespace);
        }
        return service;
    }

    public Boolean deleteService(String namespace, String name) throws BaseAppException {
        Boolean deleted = null;
        try {
            io.fabric8.kubernetes.api.model.Service service = getService(namespace, name);
            K8sResourceUtils.validateOnDelete(service);
            deleted = K8sResourceUtils.convertStatusDetails(kubeClient.services().inNamespace(namespace).withName(name).delete());
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.DELETE_SERVICE_FAILED, name, namespace);
        }

        return deleted;
    }
}