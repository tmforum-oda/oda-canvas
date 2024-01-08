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
import org.tmforum.oda.canvas.portal.component.infrastructure.CanvasErrorCode;


import io.fabric8.kubernetes.api.model.apps.Deployment;
import io.fabric8.kubernetes.client.KubernetesClient;

/**
 * 提供Kubernetes Deployment资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sDeploymentService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sDeploymentService.class);

    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取Deployment列表
     *
     * @param namespace
     * @param keyword 支持按照关键字（名称）过滤
     */
    public List<Deployment> listDeployments(String namespace, String keyword) throws BaseAppException {
        try {
            List<Deployment> deployments = kubeClient.apps().deployments().inNamespace(namespace).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return deployments;
            }
            return deployments.stream().filter(deployment -> deployment.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list deployments in namespace[{}], tenantId[{}], error: ", namespace);
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_DEPLOYMENT_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * 获取指定的Deployment
     *
     * @param namespace
     * @param name Deployment名
     * @return
     */
    public Deployment getDeployment(String namespace, String name) throws BaseAppException {
        Deployment deployment = null;
        try {
            deployment = this.getDeployment(kubeClient, namespace, name);
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_DEPLOYMENT_FAILED, name, namespace);
        }

        if (deployment == null) {
            ExceptionPublisher.publish(CanvasErrorCode.DEPLOYMENT_NOT_EXIST, name, namespace);
        }
        return deployment;
    }

    /**
     * 获取指定的Deployment
     *
     * @param kubeClient
     * @param namespace
     * @param name Deployment名
     * @return
     */
    public Deployment getDeployment(KubernetesClient kubeClient, String namespace, String name) throws BaseAppException {
        Deployment deployment = null;
        try {
            deployment = kubeClient.apps().deployments().inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_DEPLOYMENT_FAILED, name, namespace);
        }

        if (deployment == null) {
            ExceptionPublisher.publish(CanvasErrorCode.DEPLOYMENT_NOT_EXIST, name, namespace);
        }
        return deployment;
    }

    public Boolean deleteDeployment(String namespace, String name) throws BaseAppException {
        Boolean deleted = null;
        try {
            Deployment deployment = getDeployment(namespace, name);
            K8sResourceUtils.validateOnDelete(deployment);
            deleted = K8sResourceUtils.convertStatusDetails(kubeClient.apps().deployments().inNamespace(namespace).withName(name).delete());
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.DELETE_DEPLOYMENT_FAILED, name, namespace);
        }

        return deleted;
    }
}
