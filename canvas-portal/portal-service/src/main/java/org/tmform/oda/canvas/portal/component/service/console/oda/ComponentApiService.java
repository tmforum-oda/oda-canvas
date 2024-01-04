package org.tmform.oda.canvas.portal.component.service.console.oda;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmform.oda.canvas.portal.component.infrastructure.ExceptionErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;

import com.google.common.collect.Lists;
import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.dsl.base.CustomResourceDefinitionContext;

/**
 * 提供ODA Component API资源相关服务
 *
 * @author li.peilong
 * @date 2022/12/02
 */
@Service
public class ComponentApiService {
    private static final Logger LOGGER = LoggerFactory.getLogger(ComponentApiService.class);

    @Autowired
    private KubernetesClient kubeClient;

    // ODA Component API CRD信息
    private static final CustomResourceDefinitionContext ODA_COMPONENT_API_CRD_CONTEXT = new CustomResourceDefinitionContext.Builder()
            .withName("apis.oda.tmforum.org")
            .withGroup("oda.tmforum.org")
            .withScope("Namespaced")
            .withVersion("v1alpha3")
            .withPlural("apis")
            .withKind("api")
            .build();
    /**
     * 获取ODA Component的API列表
     *
     * @param namespace
     * @param componentName 组件名
     */
    public List<GenericKubernetesResource> listOdaComponentApis(String namespace, String componentName) throws BaseAppException {
        try {
            List<GenericKubernetesResource> apis = kubeClient.genericKubernetesResources(ODA_COMPONENT_API_CRD_CONTEXT).inNamespace(namespace).withLabel("oda.tmforum.org/componentName", componentName).list().getItems();
            return apis;
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list apis of oda component [{}] in namespace[{}], tenantId[{}], error: ", componentName, namespace);
            // FIXME
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, ExceptionErrorCode.ODA_LIST_COMPONENT_API_FAILED, componentName, namespace);
        }
        return Lists.newArrayList();
    }


    /**
     * 获取指定的ODA Component
     *
     * @param namespace
     * @param name Component名
     * @return
     */
    public GenericKubernetesResource getOdaComponentApi(String namespace, String name) throws BaseAppException {
        GenericKubernetesResource api = null;
        try {
            api = kubeClient.genericKubernetesResources(ODA_COMPONENT_API_CRD_CONTEXT).inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to get oda component api[{}] in namespace[{}], tenantId[{}], error: ", name, namespace);
            // FIXME
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, ExceptionErrorCode.ODA_GET_COMPONENT_API_FAILED, name, namespace);
        }

        if (api == null) {
            ExceptionPublisher.publish(ExceptionErrorCode.ODA_COMPONENT_API_NOT_EXIST, name, namespace);
        }
        return api;
    }
}
