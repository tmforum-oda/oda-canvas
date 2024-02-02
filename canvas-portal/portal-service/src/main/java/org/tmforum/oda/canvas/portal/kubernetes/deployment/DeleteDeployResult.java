package org.tmforum.oda.canvas.portal.kubernetes.deployment;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@Builder
public class DeleteDeployResult {
    private Boolean deleted;
}
