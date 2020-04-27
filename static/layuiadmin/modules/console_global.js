/** layuiAdmin.std-v1.2.1 LPPL License By http://www.layui.com/admin/ */
;
layui.define(function (e) {
    layui.use(["admin", "carousel"],
        function () {
            var e = layui.$,
                t = (layui.admin, layui.carousel),
                a = layui.element,
                i = layui.device();
            e(".layadmin-carousel").each(function () {
                var a = e(this);
                t.render({
                    elem: this,
                    width: "100%",
                    arrow: "none",
                    interval: a.data("interval"),
                    autoplay: a.data("autoplay") === !0,
                    trigger: i.ios || i.android ? "click" : "hover",
                    anim: a.data("anim")
                })
            }),
                a.render("progress")
        }),
        layui.use(["admin", "carousel", "echarts"],
            function charts() {
                var e = layui.$,
                    t = layui.admin,
                    a = layui.carousel,
                    i = layui.echarts,
                    l = [],
                    n = [
                        {
                            title: {
                                text: "媒体趋势",
                                x: "center",
                                textStyle: {
                                    fontSize: 14
                                }
                            },
                            tooltip: {
                                trigger: "axis"
                            },
                            legend: {
                                data: ["", ""]
                            },
                            xAxis: [{
                                type: "category",
                                boundaryGap: !1,
                                data: ["06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30"]
                            }],
                            yAxis: [{
                                type: "value"
                            }],
                            series: [{
                                name: "总量",
                                type: "line",
                                smooth: !0,
                                itemStyle: {
                                    normal: {
                                        color:'#ba26de',
                                        areaStyle: {
                                            type: "default"
                                        }
                                    }
                                },
                                data: [111, 222, 333, 444, 555, 666, 3333, 33333, 55555, 66666, 33333, 3333, 6666, 11888, 26666, 38888, 56666, 42222, 39999, 28888, 17777, 9666, 6555, 5555, 3333, 2222, 3111, 6999, 5888, 2777, 1666, 999, 888, 777]
                            },
                                {
                                    name: "android",
                                    type: "line",
                                    smooth: !0,
                                    itemStyle: {
                                        normal: {
                                            areaStyle: {
                                                type: "default"
                                            }
                                        }
                                    },
                                    data: [102, 343, 542, 576, 555, 532, 466, 4657, 235, 5456, 768, 235, 6453, 11888, 26666, 38888, 56666, 42222, 39999, 28888, 17777, 9666, 6555, 5555, 3333, 2222, 3111, 6999, 5888, 2777, 1666, 999, 888, 777]
                                },
                                {
                                    name: "ios",
                                    type: "line",
                                    smooth: !0,
                                    itemStyle: {
                                        normal: {
                                            color:'#ebe41c',
                                            areaStyle: {
                                                type: "default"
                                            }
                                        }
                                    },
                                    data: [11, 22, 33, 44, 55, 66, 333, 3333, 5555, 12666, 3333, 333, 666, 1188, 2666, 3888, 6666, 4222, 3999, 2888, 1777, 966, 655, 555, 333, 222, 311, 699, 588, 277, 166, 99, 88, 77]
                                }]
                        },
                        {
                            title: {
                                text: "访客浏览器分布",
                                x: "center",
                                textStyle: {
                                    fontSize: 14
                                }
                            },
                            tooltip: {
                                trigger: "item",
                                formatter: "{a} <br/>{b} : {c} ({d}%)"
                            },
                            legend: {
                                orient: "vertical",
                                x: "left",
                                data: ["Chrome", "Firefox", "IE 8.0", "Safari", "其它浏览器"]
                            },
                            series: [{
                                name: "访问来源",
                                type: "pie",
                                radius: "55%",
                                center: ["50%", "50%"],
                                data: [{
                                    value: 9052,
                                    name: "Chrome"
                                },
                                    {
                                        value: 1610,
                                        name: "Firefox"
                                    },
                                    {
                                        value: 3200,
                                        name: "IE 8.0"
                                    },
                                    {
                                        value: 535,
                                        name: "Safari"
                                    },
                                    {
                                        value: 1700,
                                        name: "其它浏览器"
                                    }]
                            }]
                        },
                        {
                            title: {
                                text: '',
                                x: 'center',
                                y: 0,
                                textStyle: {
                                    color: '#B4B4B4',
                                    fontSize: 16,
                                    fontWeight: 'normal',
                                },

                            },
                            backgroundColor: '#043065',
                            tooltip: {
                                trigger: 'axis',
                                backgroundColor: 'rgba(255,255,255,0.1)',
                                axisPointer: {
                                    type: 'shadow',
                                    label: {
                                        show: true,
                                        backgroundColor: '#7B7DDC'
                                    }
                                }
                            },
                            legend: {
                                data: ['ios', 'android', '总数',],
                                textStyle: {
                                    color: '#B4B4B4'
                                },
                                top: '7%',
                            },
                            grid: {
                                x: '12%',
                                width: '82%',
                                y: '12%',
                            },
                            xAxis: {
                                data: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
                                axisLine: {
                                    lineStyle: {
                                        color: '#B4B4B4'
                                    }
                                },
                                axisTick: {
                                    show: false,
                                },
                            },
                            yAxis: [{

                                splitLine: {show: false},
                                axisLine: {
                                    lineStyle: {
                                        color: '#B4B4B4',
                                    }
                                },

                                axisLabel: {
                                    formatter: '{value} ',
                                }
                            },
                                {

                                    splitLine: {show: false},
                                    axisLine: {
                                        lineStyle: {
                                            color: '#B4B4B4',
                                        }
                                    },
                                    axisLabel: {
                                        formatter: '{value} ',
                                    }
                                }],

                            series: [{
                                name: '总数',
                                type: 'line',
                                smooth: true,
                                showAllSymbol: true,
                                symbol: 'emptyCircle',
                                symbolSize: 8,
                                yAxisIndex: 1,
                                itemStyle: {
                                    normal: {
                                        color: '#F02FC2'
                                    },
                                },
                                data: []
                            },
                                {
                                    name: 'ios',
                                    type: 'bar',
                                    barWidth: 10,
                                    yAxisIndex: 0,
                                    itemStyle: {
                                        normal: {
                                            barBorderRadius: 5,
                                            color: '#956FD4'
                                        }
                                    },
                                    data: []
                                },
                                {
                                    name: 'android',
                                    type: 'bar',
                                    barGap: '10%',
                                    barWidth: 10,
                                    yAxisIndex: 0,
                                    itemStyle: {
                                        normal: {
                                            barBorderRadius: 5,
                                            color:'#11EE3D'
                                        }
                                    },
                                    z: -12,

                                    data: []
                                },
                            ]
                        }
                    ],
                    r = e("#LAY-index-dataview").children("div"),
                    o = function (e) {
                        l[e] = i.init(r[e], layui.echartsTheme),
                            len = date_list.length;
                        if (len > 0) {
                            n[0].title.text = media_name + "30天趋势图" + "(" + report_type + ")";
                            n[0].xAxis[0].data = date_list;
                            n[0].series[0].data = sum_data;
                            n[0].series[1].data = android_data_list;
                            n[0].series[2].data = ios_data_list;
                        }
                        n[2].title.text = media_name + "小时趋势图" + "(" + report_type + ")";
                        n[2].series[0].data = hour_sum_data;
                        n[2].series[1].data = hour_ios_list;
                        n[2].series[2].data = hour_android_list;


                        l[e].setOption(n[e], true),
                            t.resize(function () {
                                l[e].resize()
                            })
                    };

                if (r[0]) {
                    o(0);
                    var d = 0;
                    a.on("change(LAY-index-dataview)",
                        function (e) {
                            o(d = e.index)
                        }),
                        layui.admin.on("side",
                            function () {
                                setTimeout(function () {
                                        o(d)
                                    },
                                    300)
                            }),
                        layui.admin.on("hash(tab)",
                            function () {
                                layui.router().path.join("") || o(d)
                            })
                }
                ;

                window.aj = function () {
                    o(0);
                    o(1);
                    o(2);
                };
            }),
        layui.use("table",
            function () {
                var e = (layui.$, layui.table);
                e.render({
                    elem: "#LAY-index-topSearch",
                    url: layui.setter.base + "json/console/top-search.js",
                    page: !0,
                    cols: [[{
                        type: "numbers",
                        fixed: "left"
                    },
                        {
                            field: "keywords",
                            title: "关键词",
                            minWidth: 300,
                            templet: '<div><a href="https://www.baidu.com/s?wd={{ d.keywords }}" target="_blank" class="layui-table-link">{{ d.keywords }}</div>'
                        },
                        {
                            field: "frequency",
                            title: "搜索次数",
                            minWidth: 120,
                            sort: !0
                        },
                        {
                            field: "userNums",
                            title: "用户数",
                            sort: !0
                        }]],
                    skin: "line"
                }),
                    e.render({
                        elem: "#LAY-index-topCard",
                        url: layui.setter.base + "json/console/top-card.js",
                        page: !0,
                        cellMinWidth: 120,
                        cols: [[{
                            type: "numbers",
                            fixed: "left"
                        },
                            {
                                field: "title",
                                title: "标题",
                                minWidth: 300,
                                templet: '<div><a href="{{ d.href }}" target="_blank" class="layui-table-link">{{ d.title }}</div>'
                            },
                            {
                                field: "username",
                                title: "发帖者"
                            },
                            {
                                field: "channel",
                                title: "类别"
                            },
                            {
                                field: "crt",
                                title: "点击率",
                                sort: !0
                            }]],
                        skin: "line"
                    })
            }),
        e("console", {})
});