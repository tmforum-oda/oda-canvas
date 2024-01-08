package org.tmforum.oda.canvas.portal.component.controller.console.oda;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.component.service.console.oda.OdaComponentApiService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.YamlResult;

import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import io.fabric8.kubernetes.client.utils.Serialization;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

/**
 * 提供ODA API管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("oda-component-api-controller")
@RequestMapping(value = "/console/oda")
@Api(tags = "ODA Component API管理接口")
public class OdaComponentApiController {
    @Autowired
    private OdaComponentApiService odaComponentApiService;

    @GetMapping("/apis")
    @ApiOperation(value = "获取指定ODA Component的API列表")
    public ResponseEntity<List<GenericKubernetesResource>> listOdaComponentApis(@RequestParam("namespace") String namespace,
                                                                                @RequestParam("componentName") String componentName) throws BaseAppException {
        List<GenericKubernetesResource> apis = odaComponentApiService.listOdaComponentApis(namespace, componentName);
        return ResponseEntity.ok(apis);
    }

    @GetMapping("/apis/{name}")
    @ApiOperation(value = "获取指定ODA Component API")
    public ResponseEntity<GenericKubernetesResource> getOdaComponentApi(@RequestParam("namespace") String namespace,
                                                                        @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource api = odaComponentApiService.getOdaComponentApi(namespace, name);
        return ResponseEntity.ok(api);
    }

    @GetMapping("/apis/{name}/yaml")
    @ApiOperation(value = "获取指定ODA Component API的YAML")
    public ResponseEntity<YamlResult> getOdaComponentApiAsYaml(@RequestParam("namespace") String namespace,
                                                               @PathVariable("name") String name) throws BaseAppException {
        GenericKubernetesResource api = odaComponentApiService.getOdaComponentApi(namespace, name);
        String yaml = Serialization.asYaml(api);
        return ResponseEntity.ok(YamlResult.builder().data(yaml).build());
    }
}
