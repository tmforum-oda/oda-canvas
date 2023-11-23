package org.tmform.oda.canvas.portal.component.service.console.oda;

import java.io.File;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.tmform.oda.canvas.portal.component.infrastructure.ExceptionErrorCode;
import org.tmform.oda.canvas.portal.component.service.console.helm.HelmChartService;
import org.tmform.oda.canvas.portal.helm.HelmProperties;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChart;

import com.google.common.base.Joiner;

/**
 * 提供ODA Component资源相关服务
 *
 * @author li.peilong
 * @date 2023/02/06
 */
@Service
public class ComponentService {
    private static final Logger LOGGER = LoggerFactory.getLogger(ComponentService.class);
    @Autowired
    private HelmChartService helmChartService;

    @Autowired
    private HelmProperties helmProperties;

    /**
     * 获取ODA组件模板列表
     *
     * @param keyword
     * @return
     * @throws BaseAppException
     */
    public List<Component> listOdaComponents(String keyword) throws BaseAppException {
        // 仅查询ODA仓库的chart
        List<HelmChart> charts = helmChartService.listCharts(helmProperties.getReponame(), keyword);
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
     * 获取Oda组件
     *
     * @param repoName
     * @param chartName
     * @return
     */
    public Component getOdaComponent(String repoName, String chartName, String version) throws BaseAppException {
        HelmChart chart = helmChartService.getChart(Joiner.on("/").join(repoName, chartName), version);
        return Component.from(chart);
    }

    /**
     * 添加ODA组件模板
     *
     * @param tenantId
     * @param file
     */
    public void add(Integer tenantId, MultipartFile file) throws BaseAppException {
        // FIXME
        String odaRepoName = Joiner.on("-").join("tmfoda", null);
        String fileName = StringUtil.format("oda_chart-{}-{}", System.currentTimeMillis(), file.getOriginalFilename());
        File tmpUploadFile = new File("/tmp", FilenameUtils.getName(fileName));
        try {
            FileUtils.copyInputStreamToFile(file.getInputStream(), tmpUploadFile);
            helmChartService.push(tenantId, tmpUploadFile.getAbsolutePath(), odaRepoName);
        }
        catch (BaseAppException e) {
            LOGGER.warn("Failed to add oda component[{}], error: ", file.getOriginalFilename());
            // FIXME
            //LOGGER.warn(e);
            ExceptionPublisher.publish(e, ExceptionErrorCode.ODA_ADD_COMPONENT_FAILED, file.getOriginalFilename());
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e);
        }
        finally {
            // 删除临时文件
            FileUtils.deleteQuietly(tmpUploadFile);
        }

    }
}
