package org.tmforum.oda.canvas.portal.component.controller.console;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.component.service.console.oda.NamespaceService;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.Namespace;

@RestController
@RequestMapping("/console/oda")
public class NamespaceController {

    @Autowired
    private NamespaceService namespaceService;

    @GetMapping("/namespaces")
    public Namespace getNamespace(){
        return namespaceService.getNamespace();
    }
}
