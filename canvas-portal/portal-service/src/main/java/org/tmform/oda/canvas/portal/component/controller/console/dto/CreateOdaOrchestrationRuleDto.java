package org.tmform.oda.canvas.portal.component.controller.console.dto;

import java.util.List;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

import org.tmform.oda.canvas.portal.component.service.console.oda.OrchestrationRule;


/**
 * @author li.peilong
 * @date 2023/02/10
 */
public class CreateOdaOrchestrationRuleDto {
    @NotBlank
    private String name;
    @NotNull
    private Boolean enabled;
    @NotBlank
    private String plural;
    private String filter;
    private List<OrchestrationRule.EventType> events;
    @NotBlank
    private String webhookUrl;
    @NotNull
    private OrchestrationRule.FailurePolicy failurePolicy;
    @NotNull
    private OrchestrationRule.OverridePolicy overridePolicy;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Boolean getEnabled() {
        return enabled;
    }

    public void setEnabled(Boolean enabled) {
        this.enabled = enabled;
    }

    public String getPlural() {
        return plural;
    }

    public void setPlural(String plural) {
        this.plural = plural;
    }

    public String getFilter() {
        return filter;
    }

    public void setFilter(String filter) {
        this.filter = filter;
    }

    public List<OrchestrationRule.EventType> getEvents() {
        return events;
    }

    public void setEvents(List<OrchestrationRule.EventType> events) {
        this.events = events;
    }

    public String getWebhookUrl() {
        return webhookUrl;
    }

    public void setWebhookUrl(String webhookUrl) {
        this.webhookUrl = webhookUrl;
    }

    public OrchestrationRule.FailurePolicy getFailurePolicy() {
        return failurePolicy;
    }

    public void setFailurePolicy(OrchestrationRule.FailurePolicy failurePolicy) {
        this.failurePolicy = failurePolicy;
    }

    public OrchestrationRule.OverridePolicy getOverridePolicy() {
        return overridePolicy;
    }

    public void setOverridePolicy(OrchestrationRule.OverridePolicy overridePolicy) {
        this.overridePolicy = overridePolicy;
    }
}
