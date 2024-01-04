package org.tmform.oda.canvas.portal.component.service.console.oda;

import io.fabric8.kubernetes.api.model.GenericKubernetesResource;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.util.JsonPathUtil;
import org.tmforum.oda.canvas.portal.core.util.JsonUtil;

/**
 *
 * @author li.peilong
 * @date 2023/02/10
 */
@Builder
@AllArgsConstructor
public class Orchestration {
    private String name;
    private String namespace;
    private String description;
    private Date createDate;
    private List<OrchestrationRule> rules;
    /**
     * 从
     * @param orchestration
     * @return
     * @throws BaseAppException
     */
    public static Orchestration from(GenericKubernetesResource orchestration) throws BaseAppException {
        String json = JsonUtil.object2Json(orchestration);
        return Orchestration.builder()
            .name(orchestration.getMetadata().getName())
            .namespace(orchestration.getMetadata().getNamespace())
            .description(JsonPathUtil.findOne(json, "$.spec.description"))
            .rules(JsonPathUtil.findList(json, "$.spec.rules[*]", OrchestrationRule.class))
            .createDate(Date.from(Instant.parse(orchestration.getMetadata().getCreationTimestamp())))
            .build();
    }

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

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Date getCreateDate() {
        return createDate;
    }

    public void setCreateDate(Date createDate) {
        this.createDate = createDate;
    }

    public List<OrchestrationRule> getRules() {
        if (rules == null) {
            rules = new ArrayList<>();
        }
        return rules;
    }

    public void setRules(List<OrchestrationRule> rules) {
        this.rules = rules;
    }
}
