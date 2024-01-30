package org.tmforum.oda.canvas.portal.component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

import io.fabric8.kubernetes.api.model.Event;
import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import io.fabric8.kubernetes.api.model.HasMetadata;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;


/**
 * Provides ODA component instance api
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("oda-component-instance-controller")
@RequestMapping("/console/oda")
@Api(tags = "ODA Component instance api")
public class ComponentInstanceController {
    private final ComponentInstanceService componentInstanceService;

    public ComponentInstanceController(ComponentInstanceService componentInstanceService) {
        this.componentInstanceService = componentInstanceService;
    }

    @GetMapping("/instances/stats/domain")
    @ApiOperation(value = "stat component instance by domain")
    public ResponseEntity<List<ComponentInstanceDomainStatsDto>> statsOdaComponentInstancesByDomain(@RequestParam("namespace") String namespace) throws BaseAppException {
        List<ComponentInstanceSummary> instances = componentInstanceService.listOdaComponentInstancesSummary(namespace, null);
        List<ComponentType> types = Arrays.stream(ComponentType.values()).filter(odaComponentType -> odaComponentType != ComponentType.unknown).collect(Collectors.toList());
        // group by domain
        Map<String, List<ComponentType>> domainTypes = new HashMap<>();
        types.forEach(odaComponentType -> {
            if (!domainTypes.containsKey(odaComponentType.getDomain())) {
                domainTypes.put(odaComponentType.getDomain(), new ArrayList<>());
            }
            domainTypes.get(odaComponentType.getDomain()).add(odaComponentType);
        });
        // group by type
        Map<ComponentType, List<ComponentInstanceSummary>> typeInstances = new HashMap<>();
        types.forEach(type -> typeInstances.put(type, instances.stream().filter(componentInstanceSummary -> StringUtils.equals(type.getName(), componentInstanceSummary.getType())).collect(Collectors.toList())));
        List<ComponentInstanceDomainStatsDto> result = new ArrayList<>();

        for (Map.Entry<String, List<ComponentType>> entry : domainTypes.entrySet()) {
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
    @ApiOperation(value = "Lists all ODA component instances in a specified namespace, with an optional keyword for filtering.")
    public ResponseEntity<List<GenericKubernetesResource>> listOdaComponentInstances(@RequestParam("namespace") String namespace,
                                                                                     @ApiParam(value = "The name or type of the ODA component instance supports fuzzy matching.") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<GenericKubernetesResource> instances = componentInstanceService.listOdaComponentInstances(namespace, keyword);
        return ResponseEntity.ok(instances);
    }

    @GetMapping("/instances/events")
    @ApiOperation(value = "Lists events for ODA component instances in a specified namespace, with an optional component filter.")
    public ResponseEntity<List<Event>> listOdaComponentInstanceEvents(@RequestParam("namespace") String namespace,
                                                                      @ApiParam(value = "ODA Component instance name") @RequestParam(value = "component", required = false) String component) throws BaseAppException {
        List<Event> events = componentInstanceService.listOdaComponentInstanceEvents(namespace, component);
        return ResponseEntity.ok(events);
    }

    @GetMapping("/instances/{name}/events")
    @ApiOperation(value = "Retrieves a list of events for a specific ODA component instance")
    public ResponseEntity<List<Event>> getOdaComponentInstanceEvents(@RequestParam("namespace") String namespace,
                                                                     @PathVariable("name") String name) throws BaseAppException {
        List<Event> events = componentInstanceService.listOdaComponentInstanceEvents(namespace, name);
        return ResponseEntity.ok(events);
    }

    @GetMapping("/instances/{name}/resources")
    @ApiOperation(value = " Lists Kubernetes resources related to a specific ODA component instance")
    public ResponseEntity<List<HasMetadata>> listOdaComponentInstanceResources(@RequestParam("namespace") String namespace,
                                                                               @PathVariable("name") String name) throws BaseAppException {
        List<HasMetadata> resources = componentInstanceService.listOdaComponentInstanceResources(namespace, name);
        return ResponseEntity.ok(resources);
    }

    @GetMapping("/instances/summary")
    @ApiOperation(value = " Provides a summary list of ODA component instances in a specified namespace, with basic information only")
    public ResponseEntity<List<ComponentInstanceSummary>> listOdaComponentInstancesSummary(@RequestParam("namespace") String namespace,
                                                                                           @ApiParam(value = "Keywords, such as instance name, type, vendor, domain, and status, support fuzzy matching.") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<ComponentInstanceSummary> result = componentInstanceService.listOdaComponentInstancesSummary(namespace, keyword);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/instances/{name}")
    @ApiOperation(value = "Retrieves a specific ODA component instance")
    public ResponseEntity<GenericKubernetesResource> getOdaComponentInstance(@RequestParam("namespace") String namespace,
                                                                             @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource component = componentInstanceService.getOdaComponentInstance(namespace, name);
        return ResponseEntity.ok(component);
    }

    @GetMapping("/instances/{name}/summary")
    @ApiOperation(value = "Provides a summary of a specific ODA component instance, with basic information only")
    public ResponseEntity<ComponentInstanceSummary> getOdaComponentInstanceSummary(@RequestParam("namespace") String namespace,
                                                                                   @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource component = componentInstanceService.getOdaComponentInstance(namespace, name);
        ComponentInstanceSummary result = ComponentInstanceSummary.from(component);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/instances/{name}/yaml")
    @ApiOperation(value = "Retrieves the YAML representation of a specific ODA component instance")
    public ResponseEntity<YamlResult> getOdaComponentInstanceAsYaml(@RequestParam("namespace") String namespace,
                                                                    @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource component = componentInstanceService.getOdaComponentInstance(namespace, name);
        String yaml = Serialization.asYaml(component);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
