package org.tmforum.oda.canvas.portal.component;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.infrastructure.CanvasErrorCode;

import com.google.common.collect.Lists;
import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.dsl.base.CustomResourceDefinitionContext;

/**
 * Service for components api resource
 *
 * @author li.peilong
 * @date 2022/12/02
 */
@Service
public class ComponentApiService {
    private static final Logger LOGGER = LoggerFactory.getLogger(ComponentApiService.class);

    private final KubernetesClient kubeClient;

    public ComponentApiService(KubernetesClient kubeClient) {
        this.kubeClient = kubeClient;
    }

    private static final CustomResourceDefinitionContext ODA_COMPONENT_API_CRD_CONTEXT = new CustomResourceDefinitionContext.Builder()
            .withName("exposedapis.oda.tmforum.org")
            .withGroup("oda.tmforum.org")
            .withScope("Namespaced")
            .withVersion("v1")
            .withPlural("exposedapis")
            .withKind("ExposedAPI")
            .build();

    /**
     * list component api resource
     *
     * @param namespace     namespace
     * @param componentName component name
     */
    public List<GenericKubernetesResource> listOdaComponentApis(String namespace, String componentName) throws BaseAppException {
        try {
            List<GenericKubernetesResource> apis = kubeClient.genericKubernetesResources(ODA_COMPONENT_API_CRD_CONTEXT).inNamespace(namespace).withLabel("oda.tmforum.org/componentName", componentName).list().getItems();
            return apis;
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list apis of oda component [{}] in namespace[{}], tenantId[{}], error: ", componentName, namespace, e);
            ExceptionPublisher.publish(e, CanvasErrorCode.ODA_LIST_COMPONENT_API_FAILED, componentName, namespace);
        }
        return Lists.newArrayList();
    }

    /**
     * get component api resource with specified name
     *
     * @param namespace namespace
     * @param name      Component name
     * @return component api
     */
    public GenericKubernetesResource getOdaComponentApi(String namespace, String name) throws BaseAppException {
        GenericKubernetesResource api = null;
        try {
            api = kubeClient.genericKubernetesResources(ODA_COMPONENT_API_CRD_CONTEXT).inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to get oda component api[{}] in namespace[{}], tenantId[{}], error: ", name, namespace, e);
            ExceptionPublisher.publish(e, CanvasErrorCode.ODA_GET_COMPONENT_API_FAILED, name, namespace);
        }

        if (api == null) {
            ExceptionPublisher.publish(CanvasErrorCode.ODA_COMPONENT_API_NOT_EXIST, name, namespace);
        }
        return api;
    }
}
