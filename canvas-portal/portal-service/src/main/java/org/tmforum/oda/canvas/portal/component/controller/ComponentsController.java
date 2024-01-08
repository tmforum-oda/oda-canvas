package org.tmforum.oda.canvas.portal.component.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.tmforum.oda.canvas.portal.component.service.console.oda.Component;
import org.tmforum.oda.canvas.portal.component.service.console.oda.ComponentService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import com.google.common.collect.Maps;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;


/**
 * 提供ODA Component（Chart）管理相关接口
 *
 * @author li.peilong
 * @date 2023/02/06
 */
@RestController("oda-component-controller")
@RequestMapping("/console/oda")
@Api(tags = "ODA Component（Chart）管理接口")
public class ComponentsController {
    @Autowired
    private ComponentService componentService;

    @GetMapping("/components")
    @ApiOperation(value = "获取ODA Component列表")
    public ResponseEntity<List<Component>> listOdaComponents(@ApiParam(value = "关键字，比如名称、类型、Domain、厂商，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Component> components = componentService.listOdaComponents(keyword);
        return ResponseEntity.ok(components);
    }

    @GetMapping("/components/{repo}/{name}/{version:.+}")
    @ApiOperation(value = "获取ODA Component")
    public ResponseEntity<Component> getOdaComponent(@ApiParam(value = "仓库名") @PathVariable("repo") String repo,
                                                     @ApiParam(value = "组件名") @PathVariable("name") String name,
                                                     @ApiParam(value = "Chart版本") @PathVariable("version") String version) throws BaseAppException {
        Component component = componentService.getOdaComponent(repo, name, version);
        return ResponseEntity.ok(component);
    }

    @PostMapping(value = "/components", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ApiOperation(value = "添加ODA Component")
    public ResponseEntity addOdaComponent(@RequestParam("tenantId") Integer tenantId,
                                          @RequestPart("file") MultipartFile file) throws BaseAppException {
        componentService.add(tenantId, file);
        return ResponseEntity.ok(Maps.newHashMap());
    }
}
