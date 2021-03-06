/**
 * @desc 微信分享接口，前端示例
 */
var WX_SIGNATURE_API = '/wechartconfig';

var bootstrap = function () {
    $.ajax({
        url: WX_SIGNATURE_API,
        method: 'post',
        data: {
            url: location.href.split('#')[0],
            type: "signature"
        },
        dataType: "json",
        beforeSend: function(jqXHR, settings) {
            jqXHR.setRequestHeader('X-Xsrftoken', document.cookie.match("\\b_xsrf=([^;]*)\\b")[1]);
        },
   })
    .success(function(result) {
        if (result.status != "success") {
            alert('获取签名出错');
            return;
        }
        configWeixin(result.data);
    });
};

var setupWeixinShare = function (message) {
        wx.onMenuShareTimeline(message);
        wx.onMenuShareAppMessage(message);
        wx.onMenuShareQQ(message);
        wx.onMenuShareWeibo(message);
        wx.onMenuShareQZone(message);
};

var configWeixin = function (options) {
    wx.config({
        debug: false, // 开启调试模式,调用的所有api的返回值会在客户端alert出来，若要查看传入的参数，可以在pc端打开，参数信息会通过log打出，仅在pc端时才会打印。
        appId: options.appId, // 必填，公众号的唯一标识
        timestamp: options.timestamp, // 必填，生成签名的时间戳
        nonceStr: options.nonceStr, // 必填，生成签名的随机串
        signature: options.signature,// 必填，签名，见附录1
        jsApiList: [
            'onMenuShareTimeline',
            'onMenuShareAppMessage',
            'onMenuShareQQ',
            'onMenuShareWeibo',
            'onMenuShareQZone'
        ] // 必填，需要使用的JS接口列表，所有JS接口列表见附录2
    });
};

wx.error(function(res){
    console.log(res);
});

bootstrap();