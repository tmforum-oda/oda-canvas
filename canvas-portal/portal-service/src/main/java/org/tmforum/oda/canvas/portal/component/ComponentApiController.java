package org.tmforum.oda.canvas.portal.component;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

/**
 * Provides ODA component api resource API
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("oda-component-api-controller")
@RequestMapping(value = "/console/oda")
@Api(tags = "ODA Component API")
public class ComponentApiController {
    private final ComponentApiService componentApiService;

    public ComponentApiController(ComponentApiService componentApiService) {
        this.componentApiService = componentApiService;
    }

    @GetMapping("/apis")
    @ApiOperation(value = "Get the list of APIs for a specified ODA Component")
    public ResponseEntity<List<GenericKubernetesResource>> listOdaComponentApis(@RequestParam("namespace") String namespace,
                                                                                @RequestParam("componentName") String componentName) throws BaseAppException, BaseAppException {
        List<GenericKubernetesResource> apis = componentApiService.listOdaComponentApis(namespace, componentName);
        return ResponseEntity.ok(apis);
    }

    @GetMapping("/apis/{name}")
    @ApiOperation(value = "Get a specified ODA Component API")
    public ResponseEntity<GenericKubernetesResource> getOdaComponentApi(@RequestParam("namespace") String namespace,
                                                                        @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource api = componentApiService.getOdaComponentApi(namespace, name);
        return ResponseEntity.ok(api);
    }

    @GetMapping("/apis/{name}/yaml")
    @ApiOperation(value = "Get the YAML of a specified ODA Component API")
    public ResponseEntity<YamlResult> getOdaComponentApiAsYaml(@RequestParam("namespace") String namespace,
                                                               @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource api = componentApiService.getOdaComponentApi(namespace, name);
        String yaml = Serialization.asYaml(api);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
