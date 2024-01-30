package org.tmforum.oda.canvas.portal.kubernetes.svc;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@Builder
public class DeleteServiceResult {
    private Boolean deleted;
}
