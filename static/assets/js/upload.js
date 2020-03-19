$(function() {
	layui.use([ 'layer', 'element', 'form', 'upload','jquery' ], function() {
		var layer = layui.layer,
			element = layui.element,
			form = layui.form,
			upload = layui.upload;
		//创建监听函数

		var xhrOnProgress = function(fun) {
			xhrOnProgress.onprogress = fun; //绑定监听

			//使用闭包实现监听绑
			return function() {
				//通过$.ajaxSettings.xhr();获得XMLHttpRequest对象
				var xhr = $.ajaxSettings.xhr();
				//判断监听函数是否为函数
				if (typeof xhrOnProgress.onprogress !== 'function')
					return xhr;
				//如果有监听函数并且xhr对象支持绑定时就把监听函数绑定上去
				if (xhrOnProgress.onprogress && xhr.upload) {

					xhr.upload.onprogress = xhrOnProgress.onprogress;
				}
				return xhr;
			}
		};

		var uploadFile = upload.render({
			elem : '#upload', //绑定元素s
			url : '/upimg', //传接口
			exts : 'jpg|png|jpeg',//限定上传类型
			acceptMime : 'image/jpg, image/png, image/jpeg',//只筛选上述类型图片
			xhr : xhrOnProgress,
			data: {"openid":openid,"wechat_id":wechat_id}, //可选项 额外的参数，如：{id: 123, abc: 'xxx'}
			size: 1024*3,//为0为不限制大小
			//监听xhr进度，并返回给进度条
			auto:false
			,bindAction:'#upimg',

			progress : function(value) { //上传进度回调 value进度值   
				element.progress('upload_progress', value + '%') //设置页面进度条
			},
			before : function(obj) {
				//开始上传时候让进度条去除隐藏状态
				 let wechat_id = "";
				 wechat_id = $("#wechat_id").val();
				  this.data.wechat_id = wechat_id;
				$("#upload_progress").removeClass("layui-hide");
				//或者设置loading
				//layer.load(1); //去除方法为 layer.close('loading'); 或者 layer.closeAll('loading');
			},
			done : function(res, index, upload) {//在多文件上传中 每次成功将被调用一次

				layer.close(layer.index);
				if (res.code == 1) {//此处只用于单文件图片的上传，若为多图片多文件请做其他处理
					layer.msg("上传成功！");
					console.log(res.src);//回调内容src
					$("#upload_preview").html("<img alt='预览图' src='"+ res.src +"'width='230px' height='146px' />");
				}else if (res.code == 3) {
					layer.msg("请勿重复上传！");
				}else{
					layer.msg("上传失败！");
				}
				//获取当前触发上传的元素
				//var item = this.item;
			},
			error : function(index, upload) {
				//请求异常回调
				layer.close(layer.index);
				layer.confirm("上传失败，您是否要重新上传？", {
					btn : [ '确定', '取消' ],
					icon : 3,
					title : "提示"
				}, function() {
					//关闭询问框
					layer.closeAll();
					//重新调用上传方法
					uploadFile.upload();
				})
			}
		});
		
		
	}) //layui

})