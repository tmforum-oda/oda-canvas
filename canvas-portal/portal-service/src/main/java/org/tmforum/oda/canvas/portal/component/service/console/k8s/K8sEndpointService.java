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

import io.fabric8.kubernetes.api.model.Endpoints;
import io.fabric8.kubernetes.client.KubernetesClient;

/**
 * @author liu.jiang
 * @date 2022/12/12
 * @time 13:53
 */
@Service
public class K8sEndpointService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sEndpointService.class);
    
    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取Endpoint列表
     *
     * @param namespace
     * @param keyword 支持按照关键字（名称）过滤
     */
    public List<Endpoints> listEndpoints(String namespace, String keyword) throws BaseAppException {
        try {
            List<Endpoints> endpoints = kubeClient.endpoints().inNamespace(namespace).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return endpoints;
            }
            return endpoints.stream().filter(service -> service.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list endpoints in namespace[{}], tenantId[{}], error: ", namespace);
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_ENDPOINT_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * 获取指定的Endpoint
     * @param namespace
     * @param name 服务名
     * @return
     */
    public Endpoints getEndpoint(String namespace, String name) throws BaseAppException {
        Endpoints endpoint = null;
        try {
            endpoint = kubeClient.endpoints().inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_ENDPOINT_FAILED, name, namespace);
        }

        if (endpoint == null) {
            ExceptionPublisher.publish(CanvasErrorCode.ENDPOINT_NOT_EXIST, name, namespace);
        }
        return endpoint;
    }
}
