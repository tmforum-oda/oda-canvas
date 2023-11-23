package org.tmform.oda.canvas.portal.component.controller.console.helm;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.tmform.oda.canvas.portal.component.controller.console.dto.YamlResult;
import org.tmform.oda.canvas.portal.component.service.console.helm.HelmChartService;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.ChartFile;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChart;
import org.tmforum.oda.canvas.portal.helm.client.operation.chart.HelmChartMetadata;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;

import jakarta.servlet.http.HttpServletResponse;


/**
 * 提供Helm Chart管理相关接口
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@RestController("helm-chart-controller")
@RequestMapping(value = "/console/helm")
@Api(tags = "Helm Chart管理接口")
public class HelmChartController {
    @Autowired
    private HelmChartService helmChartService;
    @GetMapping("/charts")
    @ApiOperation(value = "获取Chart列表")
    public ResponseEntity<List<HelmChart>> listCharts(@ApiParam(value = "仓库名称，不设置查询所有仓库") @RequestParam(value = "repo", required = false) String repo,
                                                      @ApiParam(value = "chart名称，支持模糊匹配") @RequestParam(value = "keyword", required = false) String keyword) throws BaseAppException {
        List<HelmChart> charts = helmChartService.listCharts(repo, keyword);
        return ResponseEntity.ok(charts);
    }

    @GetMapping("/charts/{repoName}/{chartName}/versions")
    @ApiOperation(value = "获取Chart的版本列表")
    public ResponseEntity<List<HelmChart>> listVersions(@ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                                                        @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        List<HelmChart> charts = helmChartService.listVersions(name);
        return ResponseEntity.ok(charts);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/metadata")
    @ApiOperation(value = "获取Chart某版本的元数据信息")
    public ResponseEntity<HelmChartMetadata> getChartMetadata(@ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                                                              @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName,
                                                              @ApiParam(value = "chart的版本号") @PathVariable("version") String version) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        HelmChartMetadata chartMetadata = helmChartService.getMetadata(name, version);
        return ResponseEntity.ok(chartMetadata);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/values")
    @ApiOperation(value = "获取Chart某版本的values")
    public ResponseEntity<YamlResult> getValues(@ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                                                @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName,
                                                @ApiParam(value = "chart的版本号") @PathVariable("version") String version) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        String values = helmChartService.getValues(name, version);
        return ResponseEntity.ok(YamlResult.builder().data(values).build());
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/readme")
    @ApiOperation(value = "获取Chart某版本的readme")
    public ResponseEntity<String> getReadme(@ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                                                @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName,
                                                @ApiParam(value = "chart的版本号") @PathVariable("version") String version) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        String readme = helmChartService.getReadme(name, version);
        return ResponseEntity.ok(readme);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/logo")
    @ApiOperation(value = "获取Chart某版本的logo")
    public ResponseEntity<String> getLogo(@ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                                            @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName,
                                            @ApiParam(value = "chart的版本号") @PathVariable("version") String version) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        String logo = helmChartService.getLogo(name, version);
        return ResponseEntity.ok(logo);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/structure")
    @ApiOperation(value = "获取Chart某版本的目录结构")
    public ResponseEntity<List<ChartFile>> getStructure(@ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                                                        @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName,
                                                        @ApiParam(value = "chart的版本号") @PathVariable("version") String version,
                                                        @RequestParam(value = "subdirectory", required = false) String subdirectory) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        List<ChartFile> files = helmChartService.getStructure(name, version, subdirectory);
        return ResponseEntity.ok(files);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/file")
    @ApiOperation(value = "获取某版本Chart指定的文件")
    public ResponseEntity<String> getFile(@ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                                                        @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName,
                                                        @ApiParam(value = "chart的版本号") @PathVariable("version") String version,
                                                        @RequestParam("filePath") String filePath) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        String fileContent = helmChartService.getFile(name, version, filePath);
        return ResponseEntity.ok(fileContent);
    }

    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/search")
    @ApiOperation(value = "检索某版本Char定的文件")
    public ResponseEntity<List<ChartFile>> searchFiles(@ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                                                       @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName,
                                                       @ApiParam(value = "chart的版本号") @PathVariable("version") String version,
                                                       @RequestParam("keyword") String keyword) throws BaseAppException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        List<ChartFile> files = helmChartService.searchFiles(name, version, keyword);
        return ResponseEntity.ok(files);
    }


    @GetMapping("/charts/{repoName}/{chartName}/{version:.+}/pull")
    @ApiOperation(value = "pull Char")
    public void pullChart(HttpServletResponse response, @ApiParam(value = "repo名称") @PathVariable("repoName") String repoName,
                          @ApiParam(value = "chart名称") @PathVariable("chartName") String chartName,
                          @ApiParam(value = "chart的版本号") @PathVariable("version") String version) throws BaseAppException, IOException {
        String name = StringUtil.format("{}/{}", repoName, chartName);
        Path path = helmChartService.pullChart(name, version);
        response.setHeader("Content-disposition", "attachment; filename=" + path.getFileName());
        OutputStream out = response.getOutputStream();
        try {
            IOUtils.copy(Files.newInputStream(path), out);
        }
        finally {
            IOUtils.closeQuietly(out);
        }
    }


}
