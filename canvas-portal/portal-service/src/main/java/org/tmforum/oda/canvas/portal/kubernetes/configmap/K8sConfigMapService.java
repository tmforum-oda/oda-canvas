package org.tmforum.oda.canvas.portal.kubernetes.configmap;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.infrastructure.CanvasErrorCode;
import org.tmforum.oda.canvas.portal.infrastructure.K8sResourceUtils;

import io.fabric8.kubernetes.api.model.ConfigMap;
import io.fabric8.kubernetes.client.KubernetesClient;

/**
 * Provides services related to Kubernetes ConfigMap resources
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
     * Get a list of ConfigMaps
     *
     * @param namespace
     * @param keyword   Supports filtering by keyword (name)
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
            LOGGER.warn("Failed to list configmaps in namespace[{}], error: ", namespace);
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_CONFIGMAP_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * Get the specified ConfigMap
     *
     * @param namespace
     * @param name      Name of the ConfigMap
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

    /**
     * Delete the specified ConfigMap
     *
     * @param namespace
     * @param name      Name of the ConfigMap to be deleted
     * @return Boolean indicating whether the deletion was successful or not
     */
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
