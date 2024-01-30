package org.tmforum.oda.canvas.portal.component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.operation.release.HelmRelease;

/**
 * Service for ODA Canvas component
 *
 * @author li.peilong
 * @date 2022/12/12
 */
@Service
public class CanvasService {
    private final HelmClient helmClient;

    public CanvasService(HelmClient helmClient) {
        this.helmClient = helmClient;
    }

    /**
     * Get the list of Canvas service components
     *
     * @return canvas component list
     */
    public List<CanvasComponent> listCanvasComponents() throws BaseAppException {
        // Try to get ODA components from the release
        List<HelmRelease> releases = helmClient.releases().list(null);
        List<CanvasComponent> result = new ArrayList<>();
        for (HelmRelease release : releases) {
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
     * Try to resolve the Canvas component type from the release
     *
     * @param release release
     * @return component type of the release
     */
    private CanvasComponent.Type resolveCanvasComponentType(HelmRelease release) {
        Optional<CanvasComponent.Type> result = Arrays.stream(CanvasComponent.Type.values())
                .filter(type -> type.getCharts().stream()
                        .anyMatch(chart -> release.getChart().startsWith(chart)))
                .findAny();
        if (result.isPresent()) {
            return result.get();
        }
        return null;
    }

}
