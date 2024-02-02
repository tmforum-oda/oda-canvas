package org.tmforum.oda.canvas.portal.kubernetes.ingress;

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

import io.fabric8.kubernetes.api.model.networking.v1.Ingress;
import io.fabric8.kubernetes.client.KubernetesClient;

/**
 * Provides services related to Kubernetes Ingress resources
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sIngressService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sIngressService.class);

    private KubernetesClient kubeClient;

    public K8sIngressService(KubernetesClient kubeClient) {
        this.kubeClient = kubeClient;
    }

    /**
     * Get the list of Ingresses
     *
     * @param namespace
     * @param keyword   Supports filtering by keyword (name)
     */
    public List<Ingress> listIngress(String namespace, String keyword) throws BaseAppException {
        try {
            List<Ingress> ingresses = kubeClient.network().v1().ingresses().inNamespace(namespace).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return ingresses;
            }
            return ingresses.stream().filter(ingress -> ingress.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list deployments in namespace[{}], error: ", namespace, e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_INGRESS_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * Get the specified Ingress
     *
     * @param namespace
     * @param name      Ingress name
     * @return the ingress
     */
    public Ingress getIngress(String namespace, String name) throws BaseAppException {
        Ingress ingress = null;
        try {
            ingress = kubeClient.network().v1().ingresses().inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_INGRESS_FAILED, name, namespace);
        }

        if (ingress == null) {
            ExceptionPublisher.publish(CanvasErrorCode.INGRESS_NOT_EXIST, name, namespace);
        }
        return ingress;
    }

    /**
     * Deletes the specified Ingress
     *
     * @param namespace namespace
     * @param name      Ingress name
     * @return
     */
    public Boolean deleteIngress(String namespace, String name) throws BaseAppException {
        Boolean deleted = null;
        try {
            Ingress ingress = getIngress(namespace, name);
            K8sResourceUtils.validateOnDelete(ingress);
            deleted = K8sResourceUtils.convertStatusDetails(kubeClient.network().v1().ingresses().inNamespace(namespace).withName(name).delete());
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.DELETE_INGRESS_FAILED, name, namespace);
        }

        return deleted;
    }
}
