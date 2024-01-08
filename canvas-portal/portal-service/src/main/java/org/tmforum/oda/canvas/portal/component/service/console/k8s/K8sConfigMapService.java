package org.tmforum.oda.canvas.portal.component.service.console.k8s;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.component.infrastructure.K8sResourceUtils;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;

import io.fabric8.kubernetes.api.model.ConfigMap;
import io.fabric8.kubernetes.client.KubernetesClient;
import org.tmforum.oda.canvas.portal.component.infrastructure.CanvasErrorCode;

/**
 * 提供Kubernetes ConfigMap资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sConfigMapService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sConfigMapService.class);

    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取ConfigMap列表
     *
     * @param namespace
     * @param keyword 支持按照关键字（名称）过滤
     */
    public List<ConfigMap> listConfigMaps(String namespace, String keyword) throws BaseAppException {
        try {
            List<ConfigMap> configMaps = kubeClient.configMaps().inNamespace(namespace).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return configMaps;
            }
            return configMaps.stream().filter(configMap -> configMap.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list configmaps in namespace[{}], tenantId[{}], error: ", namespace);
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_CONFIGMAP_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * 获取指定的ConfigMap
     *
     * @param namespace
     * @param name ConfigMap名
     * @return
     */
    public ConfigMap getConfigMap(String namespace, String name) throws BaseAppException {
        ConfigMap configMap = null;
        try {
            configMap = kubeClient.configMaps().inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_CONFIGMAP_FAILED, name, namespace);
        }

        if (configMap == null) {
            ExceptionPublisher.publish(CanvasErrorCode.CONFIGMAP_NOT_EXIST, name, namespace);
        }
        return configMap;
    }

    public Boolean deleteConfigMap(String namespace, String name) throws BaseAppException {
        Boolean deleted = null;
        try {
            ConfigMap configMap = getConfigMap(namespace, name);
            K8sResourceUtils.validateOnDelete(configMap);
            deleted = K8sResourceUtils.convertStatusDetails(kubeClient.services().inNamespace(namespace).withName(name).delete());
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.DELETE_CONFIGMAP_FAILED, name, namespace);
        }

        return deleted;
    }
}
