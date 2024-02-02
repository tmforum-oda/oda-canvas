package org.tmforum.oda.canvas.portal.kubernetes.pod;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.infrastructure.CanvasErrorCode;

import io.fabric8.kubernetes.api.model.Pod;
import io.fabric8.kubernetes.client.KubernetesClient;

/**
 * 提供Kubernetes Pod资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sPodService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sPodService.class);

    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取Pod列表
     *
     * @param namespace
     * @param labels
     * @param keyword   支持按照关键字（名称）过滤
     */
    public List<Pod> listPods(String namespace, Map<String, String> labels, String keyword) throws BaseAppException {
        try {
            List<Pod> pods = kubeClient.pods().inNamespace(namespace).withLabels(labels == null ? Collections.emptyMap() : labels).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return pods;
            }
            return pods.stream().filter(pod -> pod.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list pods in namespace[{}], tenantId[{}], error: ", namespace);
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_POD_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * 获取指定的Pod
     *
     * @param namespace
     * @param name      Pod名
     * @return
     */
    public Pod getPod(String namespace, String name) throws BaseAppException {
        Pod pod = null;
        try {
            pod = kubeClient.pods().inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_POD_FAILED, name, namespace);
        }

        if (pod == null) {
            ExceptionPublisher.publish(CanvasErrorCode.POD_NOT_EXIST, name, namespace);
        }
        return pod;
    }
}
