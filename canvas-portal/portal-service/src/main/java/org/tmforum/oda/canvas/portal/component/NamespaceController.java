package org.tmforum.oda.canvas.portal.component;

import java.io.IOException;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


@RestController
@RequestMapping("/console/oda")
public class NamespaceController {

    @Autowired
    private NamespaceService namespaceService;

    @GetMapping("/namespaces")
    public NamespaceDto getNamespace() throws IOException {
        return namespaceService.getNamespace();
    }
}
