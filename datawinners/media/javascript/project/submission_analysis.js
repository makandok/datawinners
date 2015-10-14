DW.SubmissionAnalysisView = function(){

    var self = this;
    var tableViewOption = $("#table_view_option");
    var chartViewOption = $("#chart_view_option");
    var tableView = $("#submission_logs");
    var chartView = $('#chart_ol');
    var customizationView = $('#cust-icon');
    var isChartViewShown = false;
    var submissionTabs = new DW.SubmissionTabs();
    var chartGenerator = new DW.SubmissionAnalysisChartGenerator();

    self.init = function(){
       submissionTabs.setToAnalysisTab();
       _initializeSubmissionTable(submissionTabs);
       _initializeFilters();
       _initializeEvents();
       _initializeExport();
    };

    var _initializeExport = function () {
        var submissionLogExport = new DW.SubmissionLogExport();
        submissionLogExport.update_tab(submissionTabs.getActiveTabName());
        submissionLogExport.init();
    };

    var _initializeSubmissionTable = function(submissionTabs){
        var submission_table_options = {
            header_url: render_table_url + "/headers",
            table_source_url: render_table_url + '?type=' + submissionTabs.getActiveTabName(),
            row_check_box_visible: false,
            actions_menu: [],
            tabName: submissionTabs.getActiveTabName(),
            sortCol : 1
        };
        new DW.SubmissionLogTable(submission_table_options);
    };

    var _initializeFilters = function() {
        new DW.DateFilter(_postFilterSelection).init();
        new DW.DataSenderFilter(_postFilterSelection).init();
        new DW.SubjectFilter(_postFilterSelection).init();
        new DW.SearchTextFilter(_postFilterSelection).init();
    };

    var _postFilterSelection = function(){
      if(isChartViewShown)
        chartGenerator.generateCharts();
      else
        $(".submission_table").dataTable().fnDraw();
    };

    var _initializeEvents = function(){
        tableViewOption.on("click", _showDataTableView);
        chartViewOption.on("click", _showChartView);
    };

    var _showDataTableView = function () {
        if (!isChartViewShown)
            return;
        tableViewOption.addClass("active");
        chartViewOption.removeClass("active-right");
        customizationView.show();
        _reinitializeSubmissionTableView();
        _initializeSubmissionTable(submissionTabs);
        chartView.hide();
        isChartViewShown = false;
    };

    var _reinitializeSubmissionTableView = function(){
        tableView.show();
        $('.submission_table').dataTable().fnDestroy();
        $('.submission_table').empty();
        $('#chart_info').empty();
        $('#chart_info_2').empty();
        chartView.empty();
    };

    var _showChartView = function () {
        if (isChartViewShown)
            return;
        DW.trackEvent('chart-view', 'chart-view-link-clicked');
        tableViewOption.removeClass("active");
        chartViewOption.addClass("active-right");
        customizationView.hide();
        isChartViewShown = true;
        tableView.hide();
        chartGenerator.generateCharts();
    };

};

DW.SubmissionAnalysisChartGenerator = function(){
    var self = this;
    var chartView = $('#chart_ol');

    self.generateCharts = function(){
         $.ajax({
                "dataType": 'json',
                "type": "POST",
                "url": analysis_stats_url,
                "data": {'search_filters': JSON.stringify(filter_as_json())},
                "success": function (response) {
                       chartView.show();
                      _draw_bar_charts(response);
                },
                "error": function () {
                },
                "global": false
            });
    };

    var _draw_bar_charts = function(response){
        var $chart_ol = chartView.attr('style', 'width:' + ($(window).width() - 85) + 'px').empty();

        if (response.total == 0) {
            var html = "<span id='no_charts_here'>" + gettext("Once your Data Senders have sent in Submissions, they will appear here.") + "</span>";
            showNoSubmissionExplanation(chartView, html);
            return;
        } else if ($.isEmptyObject(response.result)){
            showNoSubmissionExplanation(chartView, gettext("You do not have any multiple choice questions (Answer Type: List of choices) to display here."));
            return;
        }

        var i = 0;
        $.each(response.result, function (index, ans) {
            drawChartBlockForQuestions(index, ans, i, $chart_ol);
            drawChart(ans, i, response.total, "");
            i++;
        });
    };
};