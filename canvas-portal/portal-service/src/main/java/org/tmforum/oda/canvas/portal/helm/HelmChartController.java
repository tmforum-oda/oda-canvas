package org.tmforum.oda.canvas.portal.helm;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import org.apache.commons.io.IOUtils;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.ChartFile;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChart;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChartMetadata;
import org.tmforum.oda.canvas.portal.yaml.YamlResult;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

import jakarta.servlet.http.HttpServletResponse;

/**
 * Provides helm chart API
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("helm-chart-controller")
@RequestMapping(value = "/console/helm")
@Api(tags = "Helm Chart API")
public class HelmChartController {
    private final HelmChartService helmChartService;

    public HelmChartController(HelmChartService helmChartService) {
        this.helmChartService = helmChartService;
    }

    @GetMapping("/charts")
    @ApiOperation(value = "List charts")
    public ResponseEntity<List<HelmChart>> listCharts(@ApiParam(value = "Repository name, if not set, query all repositories") @RequestParam(value = "repo", required = false) String repo,
                                                      @ApiParam(value = "Chart name, supports fuzzy matching") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<HelmChart> charts = helmChartService.listCharts(repo, keyword);
        return ResponseEntity.ok(charts);
    }

    @GetMapping("/charts/{repoName}/{chartName}/versions")
    @ApiOperation(value = "Get the version list of a Chart")
    public ResponseEntity<List<HelmChart>> listVersions(@ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                                                        @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        List<HelmChart> charts = helmChartService.listVersions(name);
        return ResponseEntity.ok(charts);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/metadata")
    @ApiOperation(value = "Get the metadata information of a specific version of a Chart")
    public ResponseEntity<HelmChartMetadata> getChartMetadata(@ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                                                              @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName,
                                                              @ApiParam(value = "Version of the chart") @PathVariable("version") String version) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        HelmChartMetadata chartMetadata = helmChartService.getMetadata(name, version);
        return ResponseEntity.ok(chartMetadata);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/values")
    @ApiOperation(value = "Get the values of a specific version of a Chart")
    public ResponseEntity<YamlResult> getValues(@ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                                                @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName,
                                                @ApiParam(value = "Version of the chart") @PathVariable("version") String version) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        String values = helmChartService.getValues(name, version);
        return ResponseEntity.ok(YamlResult.builder().data(values).build());
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/readme")
    @ApiOperation(value = "Get the readme of a specific version of a Chart")
    public ResponseEntity<String> getReadme(@ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                                            @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName,
                                            @ApiParam(value = "Version of the chart") @PathVariable("version") String version) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        String readme = helmChartService.getReadme(name, version);
        return ResponseEntity.ok(readme);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/logo")
    @ApiOperation(value = "Get the logo of a specific version of a Chart")
    public ResponseEntity<String> getLogo(@ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                                          @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName,
                                          @ApiParam(value = "Version of the chart") @PathVariable("version") String version) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        String logo = helmChartService.getLogo(name, version);
        return ResponseEntity.ok(logo);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/structure")
    @ApiOperation(value = "Get the directory structure of a specific version of a Chart")
    public ResponseEntity<List<ChartFile>> getStructure(@ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                                                        @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName,
                                                        @ApiParam(value = "Version of the chart") @PathVariable("version") String version,
                                                        @RequestParam(value = "subdirectory", required = false) String subdirectory) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        List<ChartFile> files = helmChartService.getStructure(name, version, subdirectory);
        return ResponseEntity.ok(files);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/file")
    @ApiOperation(value = "Get a specific file of a version of a Chart")
    public ResponseEntity<String> getFile(@ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                                          @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName,
                                          @ApiParam(value = "Version of the chart") @PathVariable("version") String version,
                                          @RequestParam("filePath") String filePath) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        String fileContent = helmChartService.getFile(name, version, filePath);
        return ResponseEntity.ok(fileContent);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/search")
    @ApiOperation(value = "Search files of a specific version of a Chart")
    public ResponseEntity<List<ChartFile>> searchFiles(@ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                                                       @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName,
                                                       @ApiParam(value = "Version of the chart") @PathVariable("version") String version,
                                                       @RequestParam("keyword") String keyword) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        List<ChartFile> files = helmChartService.searchFiles(name, version, keyword);
        return ResponseEntity.ok(files);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/pull")
    @ApiOperation(value = "Pull a Chart")
    public void pullChart(HttpServletResponse response, @ApiParam(value = "Repository name") @PathVariable("repoName") String repoName,
                          @ApiParam(value = "Chart name") @PathVariable("chartName") String chartName,
                          @ApiParam(value = "Version of the chart") @PathVariable("version") String version) throws BaseAppException, IOException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        Path path = helmChartService.pullChart(name, version);
        response.setHeader("Content-disposition", "attachment; filename=" + path.getFileName());
        OutputStream out = response.getOutputStream();
        try {
            IOUtils.copy(Files.newInputStream(path), out);
        } finally {
            IOUtils.closeQuietly(out);
        }
    }

}
