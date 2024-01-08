package org.tmforum.oda.canvas.portal.component.controller.console.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
@Builder
public class DeleteCronJobResult {
    private Boolean deleted;
}
