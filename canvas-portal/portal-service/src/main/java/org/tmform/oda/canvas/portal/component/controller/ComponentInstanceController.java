package org.tmform.oda.canvas.portal.component.controller;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmform.oda.canvas.portal.component.controller.console.dto.ComponentInstanceDomainStatsDto;
import org.tmform.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmform.oda.canvas.portal.component.service.console.oda.ComponentInstanceService;
import org.tmform.oda.canvas.portal.component.service.console.oda.ComponentInstanceSummary;
import org.tmform.oda.canvas.portal.component.service.console.oda.ComponentType;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.Event;
import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import io.fabric8.kubernetes.api.model.HasMetadata;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;


/**
 * 提供ODA Component实例管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("oda-component-instance-controller")
@RequestMapping("/console/oda")
@Api(tags = "ODA Component实例管理接口")
public class ComponentInstanceController {
    @Autowired
    private ComponentInstanceService componentInstanceService;

    @GetMapping("/instances/stats/domain")
    @ApiOperation(value = "按Domain对Component实例进行统计")
    public ResponseEntity<List<ComponentInstanceDomainStatsDto>> statsOdaComponentInstancesByDomain(@RequestParam("namespace") String namespace) throws BaseAppException {
        List<ComponentInstanceSummary> instances = componentInstanceService.listOdaComponentInstancesSummary(namespace, null);
        List<ComponentType> types = Arrays.stream(ComponentType.values()).filter(odaComponentType -> odaComponentType != ComponentType.unknown).collect(Collectors.toList());
        // 按照domain进行分组
        Map<String, List<ComponentType>> domainTypes = new HashMap<>();
        types.forEach(odaComponentType -> {
            if (!domainTypes.containsKey(odaComponentType.getDomain())) {
                domainTypes.put(odaComponentType.getDomain(), new ArrayList<>());
            }
            domainTypes.get(odaComponentType.getDomain()).add(odaComponentType);
        });
        // 获取不同类型的实例
        Map<ComponentType, List<ComponentInstanceSummary>> typeInstances = new HashMap<>();
        types.forEach(type -> typeInstances.put(type, instances.stream().filter(componentInstanceSummary -> StringUtils.equals(type.getName(), componentInstanceSummary.getType())).collect(Collectors.toList())));
        List<ComponentInstanceDomainStatsDto> result = new ArrayList<>();

        for (Map.Entry<String, List<ComponentType>> entry:domainTypes.entrySet()) {
            ComponentInstanceDomainStatsDto componentInstanceDomainStatsDto = new ComponentInstanceDomainStatsDto();
            componentInstanceDomainStatsDto.setDomain(entry.getKey());
            List<ComponentInstanceDomainStatsDto.OdaComponentTypeInstance> domainTypeInstances = new ArrayList<>();
            componentInstanceDomainStatsDto.setTypes(domainTypeInstances);
            result.add(componentInstanceDomainStatsDto);
            entry.getValue().forEach(odaComponentType -> {
                ComponentInstanceDomainStatsDto.OdaComponentTypeInstance odaComponentTypeInstance = new ComponentInstanceDomainStatsDto.OdaComponentTypeInstance();
                odaComponentTypeInstance.setType(odaComponentType.getName());
                odaComponentTypeInstance.setInstances(typeInstances.get(odaComponentType));
                domainTypeInstances.add(odaComponentTypeInstance);
            });
        }

        return ResponseEntity.ok(result);
    }

    @GetMapping("/instances")
    @ApiOperation(value = "获取指定namespace下的ODA Component实例列表")
    public ResponseEntity<List<GenericKubernetesResource>> listOdaComponentInstances(@RequestParam("namespace") String namespace,
                                                                                     @ApiParam(value = "Oda component实例名称或类型，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<GenericKubernetesResource> instances = componentInstanceService.listOdaComponentInstances(namespace, keyword);
        return ResponseEntity.ok(instances);
    }

    @GetMapping("/instances/events")
    @ApiOperation(value = "获取组件实例的事件列表")
    public ResponseEntity<List<Event>> listOdaComponentInstanceEvents(@RequestParam("namespace") String namespace,
                                                                      @ApiParam(value = "ODA Component实例名") @RequestParam(value = "component", required = false) String component) throws BaseAppException {
        List<Event> events = componentInstanceService.listOdaComponentInstanceEvents(namespace, component);
        return ResponseEntity.ok(events);
    }

    @GetMapping("/instances/{name}/events")
    @ApiOperation(value = "获取某组件实例的事件列表")
    public ResponseEntity<List<Event>> getOdaComponentInstanceEvents(@RequestParam("namespace") String namespace,
                                                                     @PathVariable("name") String name) throws BaseAppException {
        List<Event> events = componentInstanceService.listOdaComponentInstanceEvents(namespace, name);
        return ResponseEntity.ok(events);
    }

    @GetMapping("/instances/{name}/resources")
    @ApiOperation(value = "获取ODA Component实例相关的K8s资源")
    public ResponseEntity<List<HasMetadata>> listOdaComponentInstanceResources(@RequestParam("namespace") String namespace,
                                                                               @PathVariable("name") String name) throws BaseAppException {
        List<HasMetadata> resources = componentInstanceService.listOdaComponentInstanceResources(namespace, name);
        return ResponseEntity.ok(resources);
    }

    @GetMapping("/instances/summary")
    @ApiOperation(value = "获取指定namespace下的ODA Component实例列表,仅包含基本信息")
    public ResponseEntity<List<ComponentInstanceSummary>> listOdaComponentInstancesSummary(@RequestParam("namespace") String namespace,
                                                                                           @ApiParam(value = "关键字，比如实例名称、类型、厂商、domain、状态，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<ComponentInstanceSummary> result = componentInstanceService.listOdaComponentInstancesSummary(namespace, keyword);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/instances/{name}")
    @ApiOperation(value = "获取指定的ODA Component实例")
    public ResponseEntity<GenericKubernetesResource> getOdaComponentInstance(@RequestParam("namespace") String namespace,
                                                                             @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource component = componentInstanceService.getOdaComponentInstance(namespace, name);
        return ResponseEntity.ok(component);
    }

    @GetMapping("/instances/{name}/summary")
    @ApiOperation(value = "获取指定的ODA Component实例,仅包含基本信息")
    public ResponseEntity<ComponentInstanceSummary> getOdaComponentInstanceSummary(@RequestParam("namespace") String namespace,
                                                                                   @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource component = componentInstanceService.getOdaComponentInstance(namespace, name);
        ComponentInstanceSummary result = ComponentInstanceSummary.from(component);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/instances/{name}/yaml")
    @ApiOperation(value = "获取指定的ODA Component实例的YAML")
    public ResponseEntity<YamlResult> getOdaComponentInstanceAsYaml(@RequestParam("namespace") String namespace,
                                                                    @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource component = componentInstanceService.getOdaComponentInstance(namespace, name);
        String yaml = Serialization.asYaml(component);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
