package org.tmforum.oda.canvas.portal.component.service.console.k8s;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.component.infrastructure.CanvasErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.component.infrastructure.K8sResourceUtils;

import io.fabric8.kubernetes.api.model.networking.v1.Ingress;
import io.fabric8.kubernetes.client.KubernetesClient;


/**
 * 提供Kubernetes Ingresss资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sIngressService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sIngressService.class);
    
    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取ingress列表
     *
     * @param namespace
     * @param keyword 支持按照关键字（名称）过滤
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
            LOGGER.warn("Failed to list deployments in namespace[{}], tenantId[{}], error: ", namespace);
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_INGRESS_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * 获取指定的Ingress
     *
     * @param namespace
     * @param name ingress名称
     * @return
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
