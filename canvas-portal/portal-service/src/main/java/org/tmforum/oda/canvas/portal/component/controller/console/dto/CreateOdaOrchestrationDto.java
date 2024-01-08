package org.tmforum.oda.canvas.portal.component.controller.console.dto;

import java.util.ArrayList;
import java.util.List;
import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

/**
 * 创建OdaOrchestration Dto
 *
 * @author li.peilong
 * @date 2022/02/10
 */
public class CreateOdaOrchestrationDto {
    @NotBlank
    private String name;
    @NotBlank
    private String namespace;
    @NotNull
    @Min(1)
    private Integer tenantId;
    private String description;
    List<CreateOdaOrchestrationRuleDto> rules;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getNamespace() {
        return namespace;
    }

    public void setNamespace(String namespace) {
        this.namespace = namespace;
    }

    public Integer getTenantId() {
        return tenantId;
    }

    public void setTenantId(Integer tenantId) {
        this.tenantId = tenantId;
    }

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
