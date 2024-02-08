package org.tmforum.oda.canvas.portal.component;

import java.io.IOException;
import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


@RestController
@RequestMapping("/console/oda")
public class NamespaceController {

    private NamespaceService namespaceService;

    public NamespaceController(NamespaceService namespaceService) {
        this.namespaceService = namespaceService;
    }

    @GetMapping("/namespaces")
    public List<String> getNamespaces() throws IOException {
        return namespaceService.getNamespaces();
    }
}
