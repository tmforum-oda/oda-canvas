package org.tmforum.oda.canvas.portal.component.service.console.oda;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmRelease;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

/**
 * 提供ODA Canvas相关服务
 *
 * @author li.peilong
 * @date 2022/12/12
 */
@Service
public class CanvasService {
    @Autowired
    private HelmClient helmClient;

    /**
     * 获取Canvas服务组件列表
     *
     * @return
     */
    public List<CanvasComponent> listCanvasComponents() throws BaseAppException {
        // 从release中尝试获取ODA组件
        List<HelmRelease> releases = helmClient.releases().list(null);
        List<CanvasComponent> result = new ArrayList<>();
        for (HelmRelease release:releases) {
            CanvasComponent.Type type = resolveCanvasComponentType(release);
            if (type != null) {
                CanvasComponent canvasComponent = CanvasComponent.builder()
                        .name(release.getName())
                        .ready(StringUtils.equalsIgnoreCase(release.getStatus(), "deployed"))
                        .type(type)
                        .version(release.getChart())
                        .build();
                result.add(canvasComponent);
            }
        }
        return result;
    }

    /**
     * 尝试从release中解析出Canvas组件类型
     *
     * @param release
     * @return
     */
    private CanvasComponent.Type resolveCanvasComponentType(HelmRelease release) {
        Optional<CanvasComponent.Type> result = Arrays.stream(CanvasComponent.Type.values()).filter(type -> type.getCharts().stream().anyMatch(chart -> release.getChart().startsWith(chart))).findAny();
        if (result.isPresent()) {
            return result.get();
        }
        return null;
    }

}
