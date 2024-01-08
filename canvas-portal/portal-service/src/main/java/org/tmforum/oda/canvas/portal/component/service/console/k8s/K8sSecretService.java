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

import io.fabric8.kubernetes.api.model.Secret;
import io.fabric8.kubernetes.client.KubernetesClient;


/**
 * 提供Kubernetes Secret资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sSecretService {
    private static final Logger LOGGER = LoggerFactory.getLogger(K8sSecretService.class);

    @Autowired
    private KubernetesClient kubeClient;

    /**
     * 获取Secret列表
     *
     * @param namespace
     * @param keyword 支持按照关键字（名称）过滤
     */
    public List<Secret> listSecrets(String namespace, String keyword) throws BaseAppException {
        try {
            List<Secret> secrets = kubeClient.secrets().inNamespace(namespace).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return secrets;
            }
            return secrets.stream().filter(secret -> secret.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list secret in namespace[{}], tenantId[{}], error: ", namespace);
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_SECRET_FAILED, namespace);
        }
        return Collections.emptyList();
    }

    /**
     * 获取指定的Secret
     *
     * @param namespace
     * @param name Secret名
     * @return
     */
    public Secret getSecret(String namespace, String name) throws BaseAppException {
        Secret secret = null;
        try {
            secret = kubeClient.secrets().inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_SECRET_FAILED, name, namespace);
        }

        if (secret == null) {
            ExceptionPublisher.publish(CanvasErrorCode.SECRET_NOT_EXIST, name, namespace);
        }
        return secret;
    }

    public Boolean deleteSecret(String namespace, String name) throws BaseAppException {
        Boolean deleted = null;
        try {
            deleted = K8sResourceUtils.convertStatusDetails(kubeClient.apps().deployments().inNamespace(namespace).withName(name).delete());
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.DELETE_SECRET_FAILED, name, namespace);
        }

        return deleted;
    }
}
