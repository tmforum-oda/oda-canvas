package org.tmforum.oda.canvas.portal.kubernetes.ingress;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@Builder
public class DeleteIngressResult {
    private Boolean deleted;
}
