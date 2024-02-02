package org.tmforum.oda.canvas.portal.kubernetes.secret;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@Builder
public class DeleteSecretResult {
    private Boolean deleted;
}
