package org.tmforum.oda.canvas.portal.kubernetes.configmap;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@Builder
public class DeleteConfigMapResult {
    private Boolean deleted;
}
