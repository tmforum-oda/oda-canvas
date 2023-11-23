package org.tmform.oda.canvas.portal.component.controller.console.dto;

import java.util.ArrayList;
import java.util.List;

import org.tmform.oda.canvas.portal.component.controller.console.dto.CreateOdaOrchestrationRuleDto;

/**
 * 创建OdaOrchestration Dto
 *
 * @author li.peilong
 * @date 2022/02/10
 */
public class UpdateOdaOrchestrationDto {
    private String description;
    List<CreateOdaOrchestrationRuleDto> rules;

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<CreateOdaOrchestrationRuleDto> getRules() {
        if (rules == null) {
            rules = new ArrayList<>();
        }
        return rules;
    }

    public void setRules(List<CreateOdaOrchestrationRuleDto> rules) {
        this.rules = rules;
    }
}
