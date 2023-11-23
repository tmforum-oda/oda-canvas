package org.tmform.oda.canvas.portal.component.controller.console.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Builder
@Setter
@Getter
public class ComponentComplianceTestContext {

    private String podName;

    private String containerName;

    private String nodeName;

    private Integer k8sClusterId;

    private String namespace;

    private String testScriptPath;

}


