package org.tmform.oda.canvas.portal.component.service.console.oda;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmform.oda.canvas.portal.component.infrastructure.ExceptionErrorCode;
import org.tmform.oda.canvas.portal.component.service.console.helm.HelmReleaseService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.core.util.JsonPathUtil;
import org.tmforum.oda.canvas.portal.core.util.JsonUtil;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmRelease;

import com.google.common.collect.Lists;
import io.fabric8.kubernetes.api.model.Event;
import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import io.fabric8.kubernetes.api.model.HasMetadata;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.dsl.base.CustomResourceDefinitionContext;


/**
 * 提供ODA Component资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 * @see "https://rohaan.medium.com/handling-kubernetes-custom-resources-in-java-using-fabric8-kubernetes-client-249c4fe01d27"
 * @see "https://github.com/tmforum-oda/oda-canvas-charts/blob/master/canvas/charts/crds/templates/oda-component-crd.yaml"
 * @see "https://github.com/tmforum-oda/oda-ca-docs/blob/master/ODAComponentDesignGuidelines.md"
 */
@Service
public class ComponentInstanceService {
    private static final Logger LOGGER = LoggerFactory.getLogger(ComponentInstanceService.class);
    @Autowired
    private HelmReleaseService helmReleaseService;

    @Autowired
    private KubernetesClient kubeClient;

    private Map<Integer, CustomResourceDefinitionContext> customResourceDefinitionContexts = new ConcurrentHashMap<>();
    private static final String[] SUPPORTED_VERSIONS = new String[] {"v1beta1", "v1alpha4", "v1alpha3", "v1alpha2", "v1alpha1"};

    /**
     * 获取ODA Component列表
     *
     * @param namespace
     * @param keyword 支持按照关键字（名称或类型）过滤
     */
    public List<GenericKubernetesResource> listOdaComponentInstances(String namespace, String keyword) throws BaseAppException {
        try {
            List<GenericKubernetesResource> components = kubeClient.genericKubernetesResources(getCustomResourceDefinitionContext()).inNamespace(namespace).list().getItems();
            if (StringUtils.isBlank(keyword)) {
                return components;
            }
            return components.stream().filter(component -> {
                if (StringUtils.containsIgnoreCase(component.getMetadata().getName(), keyword)) {
                    return true;
                }
                try {
                    ComponentType type = ComponentType.from(JsonPathUtil.findOne(JsonUtil.object2Json(component), "$.spec.type"));
                    return StringUtils.containsIgnoreCase(type.getName(), keyword);
                }
                catch (Exception e) {
                    return false;
                }
            }).collect(Collectors.toList());
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list oda component instances in namespace[{}], tenantId[{}], error: ", namespace);
            //LOGGER.warn(e);
           // ExceptionPublisher.publish(e, AppExceptionErrorCode.ODA_LIST_COMPONENT_INSTANCE_FAILED, namespace, tenantId);
        }
        return Lists.newArrayList();
    }

    /**
     *
     * @param namespace
     * @param component 组件名，未指定则查询所有组件的事件
     * @return
     * @throws BaseAppException
     */
    public List<Event> listOdaComponentInstanceEvents(String namespace, String component) throws BaseAppException {
        try {
            Map<String, String> fields = new HashMap<>();
            fields.put("involvedObject.kind", "component");
            if (StringUtils.isNoneBlank(component)) {
                fields.put("involvedObject.name", component);
            }
            return kubeClient.v1().events().inNamespace(namespace).withFields(fields).list().getItems();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to list component instance events in namespace[{}], tenantId[{}], error: ", namespace);
            // FIXME
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, ExceptionErrorCode.ODA_LIST_COMPONENT_INSTANCE_EVENTS_FAILED, namespace);
        }
        return Lists.newArrayList();
    }

    /**
     *
     * @param namespace
     * @param keyword
     * @return
     * @throws BaseAppException
     */
    public List<ComponentInstanceSummary> listOdaComponentInstancesSummary(String namespace, String keyword) throws BaseAppException {
        List<GenericKubernetesResource> components = listOdaComponentInstances(namespace, "");
        List<ComponentInstanceSummary> result = new ArrayList<>();
        for (GenericKubernetesResource component:components) {
            result.add(ComponentInstanceSummary.from(component));
        }
        // 去掉无release或release不存在的组件实例
        List<HelmRelease> helmReleases = helmReleaseService.listReleases(namespace, keyword);
        if(CollectionUtils.isEmpty(helmReleases)){
            return Collections.emptyList();
        }

        Set<String> releases = helmReleases.stream().map(release -> release.getName()).collect(Collectors.toSet());
        return result.stream()
            .filter(componentInstanceSummary -> StringUtils.isNoneBlank(componentInstanceSummary.getRelease()) && releases.contains(componentInstanceSummary.getRelease()))
            .filter(componentInstanceSummary -> {
                return StringUtils.isBlank(keyword)
                    || StringUtils.containsIgnoreCase(componentInstanceSummary.getName(), keyword)
                    || StringUtils.contains(componentInstanceSummary.getType(), keyword)
                    || StringUtils.containsIgnoreCase(componentInstanceSummary.getVendor(), keyword)
                    || StringUtils.containsIgnoreCase(componentInstanceSummary.getDomain(), keyword)
                    || StringUtils.containsIgnoreCase(componentInstanceSummary.getStatus(), keyword);
            }).collect(Collectors.toList());
    }

    /**
     * 获取组件关联的K8S资源
     *
     * @param namespace
     * @param name
     * @return
     * @throws BaseAppException
     * @see "https://github.com/tmforum-oda/oda-ca-docs/blob/master/ODAComponentDesignGuidelines.md#step-2-add-labels-to-all-the-standard-kubernetes-resources"
     */
    public List<HasMetadata> listOdaComponentInstanceResources(String namespace, String name) throws BaseAppException {
        GenericKubernetesResource component = getOdaComponentInstance(namespace, name);
        String componentData = JsonUtil.object2Json(component);
        String selectorLabelValue = getComponentName(componentData);
        // 获取组件相关的K8S资源类型,TODO:有没有更好的方法
        List<String> kinds = getComponentResourceKinds(componentData);
        List<HasMetadata> resources = new ArrayList<>();
        // Make services, deployments, persistentvolumeclaims, jobs, cronjobs, statefulsets, configmap, secret, serviceaccount, role, rolebinding children of the component
        // These are resources that we support in a component. There are resources that we don't support
        // 参考：https://github.com/tmforum-oda/oda-ca/blob/master/controllers/componentOperator/componentOperator.py
        String selectorLabelKey = "oda.tmforum.org/componentName";
        if (kinds.contains("Service")) {
            resources.addAll(kubeClient.services().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("Deployment")) {
            resources.addAll(kubeClient.apps().deployments().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("StatefulSet")) {
            resources.addAll(kubeClient.apps().statefulSets().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("DaemonSet")) {
            resources.addAll(kubeClient.apps().daemonSets().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("ConfigMap")) {
            resources.addAll(kubeClient.configMaps().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("Secret")) {
            resources.addAll(kubeClient.secrets().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("ServiceAccount")) {
            resources.addAll(kubeClient.serviceAccounts().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("PersistentVolumeClaim")) {
            resources.addAll(kubeClient.persistentVolumeClaims().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("CronJob")) {
            resources.addAll(kubeClient.batch().v1().cronjobs().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("Job")) {
            resources.addAll(kubeClient.batch().v1().jobs().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("Role")) {
            resources.addAll(kubeClient.rbac().roles().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        if (kinds.contains("RoleBinding")) {
            resources.addAll(kubeClient.rbac().roleBindings().inNamespace(namespace).withLabel(selectorLabelKey, selectorLabelValue).list().getItems());
        }
        return resources;
    }

    /**
     * 获取组件的名称
     *
     * @param componentData
     * @return
     * @throws BaseAppException
     */
    private String getComponentName(String componentData) throws BaseAppException {
        String jsonPath = "$['metadata']['labels']['oda.tmforum.org/componentName']";
        try {
            return JsonPathUtil.findOne(componentData, jsonPath);
        }
        catch (Exception e) {
            jsonPath = "$['spec']['selector']['matchLabels']['oda.tmforum.org/componentName']";
            return JsonPathUtil.findOne(componentData, jsonPath);
        }
    }

    /**
     * 获取组件包含的资源类型
     *
     * @param componentData
     * @return
     * @throws BaseAppException
     */
    private List<String> getComponentResourceKinds(String componentData) {
        try {
            return JsonPathUtil.findList(componentData, "$['spec']['componentKinds'][*]['kind']", String.class);
        }
        catch (Exception e) {
            // FIXME
            //LOGGER.warn(e);
            // 默认包含所有类型的资源
            return Arrays.asList("Service", "Deployment", "RoleBinding", "Role", "Job", "CronJob", "PersistentVolumeClaim", "ServiceAccount", "Secret", "ConfigMap", "DaemonSet", "StatefulSet");
        }
    }

    /**
     * 获取指定的ODA Component
     *
     * @param namespace
     * @param name Component名
     * @return
     */
    public GenericKubernetesResource getOdaComponentInstance(String namespace, String name) throws BaseAppException {
        GenericKubernetesResource component = null;
        try {
            component = kubeClient.genericKubernetesResources(getCustomResourceDefinitionContext()).inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to get oda component instance[{}] in namespace[{}], tenantId[{}], error: ", name, namespace);
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, ExceptionErrorCode.ODA_GET_COMPONENT_INSTANCE_FAILED, name, namespace);
        }

        if (component == null) {
            ExceptionPublisher.publish(ExceptionErrorCode.ODA_COMPONENT_INSTANCE_NOT_EXIST, name, namespace);
        }
        return component;
    }

    public CustomResourceDefinitionContext getCustomResourceDefinitionContext() throws BaseAppException {
        synchronized (customResourceDefinitionContexts) {
            for (String version:SUPPORTED_VERSIONS) {
                CustomResourceDefinitionContext customResourceDefinitionContext = new CustomResourceDefinitionContext.Builder()
                    .withName("components.oda.tmforum.org")
                    .withGroup("oda.tmforum.org")
                    .withScope("Namespaced")
                    .withVersion(version)
                    .withPlural("components")
                    .withKind("component")
                    .build();
                try {
                    kubeClient.genericKubernetesResources(customResourceDefinitionContext).list();
                    return customResourceDefinitionContext;
                }
                catch (Exception e) {
                    LOGGER.warn("Version of CRD components.oda.tmforum.org resource is not {}, try another one, error: {}", version, e.getMessage());
                }
            }
        }
        ExceptionPublisher.publish(ExceptionErrorCode.ODA_UNSUPPORTED);
        return null;
    }

}
