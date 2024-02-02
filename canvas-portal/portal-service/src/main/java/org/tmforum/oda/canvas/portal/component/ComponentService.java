package org.tmforum.oda.canvas.portal.component;

import java.io.File;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.tmforum.oda.canvas.portal.configuration.HelmProperties;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;
import org.tmforum.oda.canvas.portal.helm.HelmChartService;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChart;
import org.tmforum.oda.canvas.portal.infrastructure.CanvasErrorCode;

import com.google.common.base.Joiner;

/**
 * Provides services related to ODA Component resources.
 *
 * @author li.peilong
 * @date 2023/02/06
 */
@Service
public class ComponentService {
    private static final Logger LOGGER = LoggerFactory.getLogger(ComponentService.class);

    private final HelmChartService helmChartService;

    private final HelmProperties helmProperties;

    public ComponentService(HelmChartService helmChartService, HelmProperties helmProperties) {
        this.helmChartService = helmChartService;
        this.helmProperties = helmProperties;
    }

    /**
     * Retrieves a list of ODA component templates.
     *
     * @param keyword keyword
     * @return
     * @throws BaseAppException
     */
    public List<Component> listOdaComponents(String keyword) throws BaseAppException {
        // Only query charts from the ODA repository
        List<HelmChart> charts = helmChartService.listCharts(helmProperties.getRepoName(), keyword);
        List<Component> components = charts.stream()
                .map(chart -> Component.from(chart))
                .filter(component -> component != Component.NULL)
                .collect(Collectors.toList());
        if (StringUtils.isBlank(keyword)) {
            return components;
        }
        return components.stream()
                .filter(component -> {
                    return StringUtils.containsIgnoreCase(component.getType(), keyword)
                            || StringUtils.containsIgnoreCase(component.getName(), keyword)
                            || StringUtils.containsIgnoreCase(component.getVendor(), keyword)
                            || StringUtils.containsIgnoreCase(component.getDomain(), keyword);
                }).collect(Collectors.toList());
    }

    /**
     * Retrieves an Oda component.
     *
     * @param repoName  repo name
     * @param chartName chart name
     * @return component
     */
    public Component getOdaComponent(String repoName, String chartName, String version) throws BaseAppException {
        HelmChart chart = helmChartService.getChart(Joiner.on("/").join(repoName, chartName), version);
        return Component.from(chart);
    }

    /**
     * Adds an ODA component template.
     *
     * @param file
     */
    public void add(MultipartFile file) throws BaseAppException {
        // FIXME
        String odaRepoName = Joiner.on("-").join("tmfoda", null);
        String fileName = StringUtil.format("oda_chart-{}-{}", System.currentTimeMillis(), file.getOriginalFilename());
        File tmpUploadFile = new File("/tmp", FilenameUtils.getName(fileName));
        try {
            FileUtils.copyInputStreamToFile(file.getInputStream(), tmpUploadFile);
            helmChartService.push(tmpUploadFile.getAbsolutePath(), odaRepoName);
        }
        catch (BaseAppException e) {
            LOGGER.warn("Failed to add oda component[{}], error: ", file.getOriginalFilename(), e);
            ExceptionPublisher.publish(e, CanvasErrorCode.ODA_ADD_COMPONENT_FAILED, file.getOriginalFilename());
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e);
        } finally {
            FileUtils.deleteQuietly(tmpUploadFile);
        }
    }
}
