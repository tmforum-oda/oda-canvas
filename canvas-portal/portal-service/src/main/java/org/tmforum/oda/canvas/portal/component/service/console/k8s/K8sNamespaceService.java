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

import io.fabric8.kubernetes.api.model.Namespace;
import io.fabric8.kubernetes.client.KubernetesClient;


/**
 * 提供Kubernetes Namespace资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sNamespaceService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sNamespaceService.class);

    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取Namespace列表
     *
     * @param keyword 支持按照关键字（名称）过滤
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
            LOGGER.warn("Failed to list namespaces, error: ");
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_NAMESPACE_FAILED);
        }
        return Collections.emptyList();
    }

    /**
     * 获取指定的Namespace
     *
     * @param name Namespace名
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
