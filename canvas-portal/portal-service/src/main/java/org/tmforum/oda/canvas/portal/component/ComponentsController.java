package org.tmforum.oda.canvas.portal.component;

import java.util.List;

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
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import com.google.common.collect.Maps;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;


/**
 * Provides ODA Component (Chart) management API
 *
 * @author li.peilong
 * @date 2023/02/06
 */
@RestController("oda-component-controller")
@RequestMapping("/console/oda")
@Api(tags = "ODA Component (Chart) Management API")
public class ComponentsController {
    private final ComponentService componentService;

    public ComponentsController(ComponentService componentService) {
        this.componentService = componentService;
    }

    @GetMapping("/components")
    @ApiOperation(value = "Get ODA Component list")
    public ResponseEntity<List<Component>> listOdaComponents(@ApiParam(value = "Keywords, such as name, type, domain, manufacturer, supports fuzzy matching") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<Component> components = componentService.listOdaComponents(keyword);
        return ResponseEntity.ok(components);
    }

    @GetMapping("/components/{repo}/{name}/{version:.+}")
    @ApiOperation(value = "Get ODA Component")
    public ResponseEntity<Component> getOdaComponent(@ApiParam(value = "Repository name") @PathVariable("repo") String repo,
                                                     @ApiParam(value = "Component name") @PathVariable("name") String name,
                                                     @ApiParam(value = "Chart version") @PathVariable("version") String version) throws BaseAppException {
        Component component = componentService.getOdaComponent(repo, name, version);
        return ResponseEntity.ok(component);
    }

    @PostMapping(value = "/components", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ApiOperation(value = "Add ODA Component")
    public ResponseEntity addOdaComponent(@RequestPart("file") MultipartFile file) throws BaseAppException {
        componentService.add(file);
        return ResponseEntity.ok(Maps.newHashMap());
    }
}
