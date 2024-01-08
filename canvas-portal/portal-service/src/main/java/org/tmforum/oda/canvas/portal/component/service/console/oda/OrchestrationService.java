package org.tmforum.oda.canvas.portal.component.service.console.oda;

import io.fabric8.kubernetes.api.model.Event;
import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import io.fabric8.kubernetes.api.model.ObjectMeta;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.dsl.base.CustomResourceDefinitionContext;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.CreateOdaOrchestrationDto;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.UpdateOdaOrchestrationDto;
import org.tmforum.oda.canvas.portal.component.infrastructure.CanvasErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.core.util.JsonUtil;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import com.google.common.collect.Lists;

/**
 * 提供ODA Orchestration资源相关服务
 *
 * @author li.peilong
 * @date 2023/02/08
 */
@Service
public class OrchestrationService {
    private static final Logger LOGGER = LoggerFactory.getLogger(OrchestrationService.class);

    @Autowired
    private KubernetesClient kubeClient;

    // ODA Orchestration CRD信息
    private static final CustomResourceDefinitionContext ODA_ORCHESTRATION_CRD_CONTEXT = new CustomResourceDefinitionContext.Builder()
            .withName("orchestrations.oda.tmforum.org")
            .withGroup("oda.tmforum.org")
            .withScope("Namespaced")
            .withVersion("v1alpha1")
            .withPlural("orchestrations")
            .withKind("Orchestration")
            .build();

    /**
     * 获取ODA Orchestration资源列表
     *
     * @param tenantId
     * @param namespace
     * @param keyword 支持按照关键字（名称）过滤
     * @return
     * @throws BaseAppException
     */
    public List<GenericKubernetesResource> listOdaOrchestrationResources(Integer tenantId, String namespace, String keyword) throws BaseAppException {
        try {
            List<GenericKubernetesResource> orchestrations = kubeClient.genericKubernetesResources(ODA_ORCHESTRATION_CRD_CONTEXT).inNamespace(namespace).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return orchestrations;
            }
            return orchestrations.stream().filter(orchestration -> orchestration.getMetadata().getName().contains(keyword)).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list oda orchestrations in namespace[{}], tenantId[{}], error: ", namespace, tenantId);
            // FIXME
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.ODA_LIST_ORCHESTRATION_FAILED, namespace, tenantId);
        }
        return Lists.newArrayList();
    }

    /**
     * 获取ODA Orchestration列表
     *
     * @param tenantId
     * @param namespace
     * @param keyword
     * @return
     * @throws BaseAppException
     */
    public List<Orchestration> listOdaOrchestrations(Integer tenantId, String namespace, String keyword) throws BaseAppException {
        List<GenericKubernetesResource> resources = listOdaOrchestrationResources(tenantId, namespace, keyword);
        List<Orchestration> result = new ArrayList<>();
        for (GenericKubernetesResource resource:resources) {
            try {
                Orchestration orchestration = Orchestration.from(resource);
                result.add(orchestration);
            }
            catch (Exception e) {
                LOGGER.warn("Failed to convert[{}] to OdaOrchestration, error: ", JsonUtil.object2Json(resource));
                // FIXME
                //LOGGER.warn(e);
            }
        }
        return result;
    }

    /**
     *
     * @param namespace
     * @param orchestration orchestration名
     * @return
     * @throws BaseAppException
     */
    public List<Event> getOdaOrchestrationEvents(String namespace, String orchestration) throws BaseAppException {
        try {
            Map<String, String> fields = new HashMap<>();
            fields.put("involvedObject.kind", "orchestration");
            fields.put("involvedObject.name", orchestration);
            return kubeClient.v1().events().inNamespace(namespace).withFields(fields).list().getItems();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list events of orchestration[{}] in namespace[{}], tenantId[{}], error: ", orchestration, namespace);
            // FIXME
            // LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.LIST_ODA_ORCHESTRATION_EVENTS_FAILED, orchestration, namespace);
        }
        return Lists.newArrayList();
    }

    /**
     * 检查某个Orchestration资源是否存在
     *
     * @param namespace
     * @param name
     * @return
     * @throws BaseAppException
     */
    public GenericKubernetesResource checkOdaOrchestrationResourceExist(String namespace, String name) throws BaseAppException {
        GenericKubernetesResource resource = null;
        try {
            resource = kubeClient.genericKubernetesResources(ODA_ORCHESTRATION_CRD_CONTEXT).inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to get oda orchestration [{}] in namespace[{}], tenantId[{}], error: ", name, namespace);
            //LOGGER.warn(e);
            // FIXME
            ExceptionPublisher.publish(e, CanvasErrorCode.ODA_GET_ORCHESTRATION_FAILED, name, namespace);
        }

        if (resource != null) {
            return resource;
        }
        ExceptionPublisher.publish(CanvasErrorCode.ODA_ORCHESTRATION_NOT_EXIST, name, namespace);
        return new GenericKubernetesResource();
    }

    /**
     * 获取Oda Orchestration Resource
     *
     * @param namespace
     * @param name
     * @return
     * @throws BaseAppException
     */
    public Orchestration getOdaOrchestration(String namespace, String name) throws BaseAppException {
        GenericKubernetesResource resource = checkOdaOrchestrationResourceExist(namespace, name);
        return Orchestration.from(resource);
    }

    /**
     * 删除orchestration
     *
     * @param namespace
     * @param name
     */
    public void deleteOdaOrchestration(String namespace, String name) throws BaseAppException {
        kubeClient.genericKubernetesResources(ODA_ORCHESTRATION_CRD_CONTEXT).inNamespace(namespace).withName(name).delete();
    }

    /**
     * 创建OdaOrchestration
     *
     * @param createOdaOrchestrationDto
     * @return
     */
    public void createOdaOrchestration(CreateOdaOrchestrationDto createOdaOrchestrationDto) throws BaseAppException {
        GenericKubernetesResource resource = new GenericKubernetesResource();
        resource.setKind("Orchestration");
        resource.setApiVersion("oda.tmforum.org/v1alpha1");

        ObjectMeta metadata = new ObjectMeta();
        metadata.setName(createOdaOrchestrationDto.getName());
        metadata.setNamespace(createOdaOrchestrationDto.getNamespace());
        resource.setMetadata(metadata);
        Map<String, Object> spec = new HashMap<>();
        spec.put("description", createOdaOrchestrationDto.getDescription());
        spec.put("rules", createOdaOrchestrationDto.getRules());
        resource.setAdditionalProperty("spec", spec);
        try {
            kubeClient.genericKubernetesResources(ODA_ORCHESTRATION_CRD_CONTEXT)
                .inNamespace(createOdaOrchestrationDto.getNamespace())
                .create(resource);
        }
        catch (Exception e) {
            LOGGER.warn("Failed to create oda orchestration [{}] in namespace[{}], tenantId[{}], error: ",
                createOdaOrchestrationDto.getName(), createOdaOrchestrationDto.getNamespace(), createOdaOrchestrationDto.getTenantId());
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.ODA_CREATE_ORCHESTRATION_FAILED, createOdaOrchestrationDto.getName(), createOdaOrchestrationDto.getNamespace(), createOdaOrchestrationDto.getTenantId());
        }
    }

    /**
     * 更新OdaOrchestration
     *
     * @param namespace
     * @param name
     * @param updateOdaOrchestrationDto
     * @throws BaseAppException
     */
    public void updateOdaOrchestration(String namespace, String name, UpdateOdaOrchestrationDto updateOdaOrchestrationDto) throws BaseAppException {
        GenericKubernetesResource resource = checkOdaOrchestrationResourceExist(namespace, name);
        Map<String, Object> spec = new HashMap<>();
        spec.put("description", updateOdaOrchestrationDto.getDescription());
        spec.put("rules", updateOdaOrchestrationDto.getRules());
        resource.setAdditionalProperty("spec", spec);
        try {
            kubeClient.genericKubernetesResources(ODA_ORCHESTRATION_CRD_CONTEXT)
                .inNamespace(namespace)
                .resource(resource).patch();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to update oda orchestration [{}] in namespace[{}], tenantId[{}], error: ", name, namespace);
            // FIXME
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, CanvasErrorCode.ODA_UPDATE_ORCHESTRATION_FAILED, name, namespace);
        }
    }
}
