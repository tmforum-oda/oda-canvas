package org.tmform.oda.canvas.portal.component.service.console.oda;

import java.util.List;

/**
 * OdaOrchestrationRule
 *
 * @author li.peilong
 * @date 2023/02/10
 */
public class OrchestrationRule {
    private String name;
    private Boolean enabled;
    private String plural;
    private String filter;
    private List<EventType> events;
    private String webhookUrl;
    private FailurePolicy failurePolicy;
    private OverridePolicy overridePolicy;


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

    public String getWebhookUrl() {
        return webhookUrl;
    }

    public void setWebhookUrl(String webhookUrl) {
        this.webhookUrl = webhookUrl;
    }

    public List<EventType> getEvents() {
        return events;
    }

    public void setEvents(List<EventType> events) {
        this.events = events;
    }

    public FailurePolicy getFailurePolicy() {
        return failurePolicy;
    }

    public void setFailurePolicy(FailurePolicy failurePolicy) {
        this.failurePolicy = failurePolicy;
    }

    public OverridePolicy getOverridePolicy() {
        return overridePolicy;
    }

    public void setOverridePolicy(OverridePolicy overridePolicy) {
        this.overridePolicy = overridePolicy;
    }

    /**
     * 合并策略
     */
    public enum OverridePolicy {
        merge, replace
    }

    /**
     * 失败处理策略
     */
    public enum FailurePolicy {
        ignore, retry, none;
    }

    /**
     * 规则关联的事件类型
     */
    public enum EventType {
        create, update, delete
    }
}
