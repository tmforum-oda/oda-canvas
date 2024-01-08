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
import org.tmforum.oda.canvas.portal.component.infrastructure.K8sResourceUtils;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;

import io.fabric8.kubernetes.client.KubernetesClient;



/**
 * 提供Kubernetes Service资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sServiceService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sServiceService.class);
    
    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取Service列表
     *
     * @param namespace
     * @param keyword 支持按照关键字（名称）过滤
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
            LOGGER.warn("Failed to list services in namespace[{}], tenantId[{}], error: ", namespace);
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_SERVICE_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * 获取指定的Service
     *
     * @param namespace
     * @param name 服务名
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
