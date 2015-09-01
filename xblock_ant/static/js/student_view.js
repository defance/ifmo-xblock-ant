function AntXBlockShow(runtime, element)
{
    function openTestWindow() {
      var testWindow = window.open('#', 'windowDLC_TEST','height=600,width=800,modal=no,fullscreen=0,status=1,location=1,scrollbars=1', true);
      testWindow.focus();
    }


    function xblock($, _)
    {
        var urls = {
            start: runtime.handlerUrl(element, 'start_lab'),
            check: runtime.handlerUrl(element, 'check_lab'),
            get_state: runtime.handlerUrl(element, 'get_user_data')
        };

        var get_template = function(tmpl){
            return _.template($(element).find(tmpl).text());
        };

        var template = {
            main: get_template('#template-ant-block')
        };


        function renderStaffInfo(data)
        {
            $(element).find('#staff-info').html(template.staff.info(data)).data(data);
        }

        function disable_controllers(context)
        {
            $(context).find(".controllers").find("button").toggleClass('disabled').attr("disabled", "disabled");
        }

        function render(data) {
            $(element).find('.ant-content').html(template.main(data));
        }

        $(function($) { // onLoad

            var block = $(element).find(".ant-block");
            var state = block.attr("data-student-state");

            var is_staff = block.attr("data-is-staff") == "True";
            if (is_staff) {
                $(element).find('.instructor-info-action').leanModal();
            }

            var data = JSON.parse(state);
            data.urls = urls;
            render(data);

            /*
             * Start lab handler.
             */
            $(element).find('.ant-start-lab').on('click', function(e) {
                var lab_window_settings = [
                    'height=600',
                    'width=800',
                    'modal=no',
                    'fullscreen=0',
                    'status=1',
                    'location=1',
                    'scrollbars=1'
                ].join();
                var lab_window = window.open(urls.start, 'windowDLC_TEST', lab_window_settings, true);
                var interval = window.setInterval(function() {
                    try {
                        if (lab_window == null || lab_window.closed) {
                            window.clearInterval(interval);
                            $(element).find('.ant-check-lab').click();
                        }
                    }
                    catch (e) {
                    }
                }, 500);
                lab_window.focus();
            });

            $(element).find('.ant-check-lab').on('click', function(e) {
                $.ajax({ url: urls.check, type: "POST", data: '{}', success: function(data){ console.log(data); }});
            });

            $(element).find('.staff-get-state-btn').on('click', function(e) {
                var data = {
                    'user_id': $(element).find('input[name="user"]').val()
                };
                $.ajax({ url: urls.get_state, type: "POST", data: JSON.stringify(data), success: function(data){
                    var deplainify = function(obj) {
                        for (var key in obj) {
                            try {
                                if (obj.hasOwnProperty(key)) {
                                    obj[key] = deplainify(JSON.parse(obj[key]));
                                }
                            } catch (e) {

                            }
                        }
                        return obj;
                    };
                    var state = deplainify(data);
                    $(element).find('.staff-info-container').html('<pre>'+ JSON.stringify(state, null, '  ') +'</pre>')
                }});
            });

        });

    }

    /**
     * The following initialization code is taken from edx-SGA XBlock.
     */
    if (require === undefined) {
        /**
         * The LMS does not use require.js (although it loads it...) and
         * does not already load jquery.fileupload.  (It looks like it uses
         * jquery.ajaxfileupload instead.  But our XBlock uses
         * jquery.fileupload.
         */
        function loadjs(url) {
            $("<script>")
                .attr("type", "text/javascript")
                .attr("src", url)
                .appendTo(element);
        }
        loadjs("/static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport.js");
        loadjs("/static/js/vendor/jQuery-File-Upload/js/jquery.fileupload.js");
        xblock($, _);
    }
    else {
        /**
         * Studio, on the other hand, uses require.js and already knows about
         * jquery.fileupload.
         */
        require(["jquery", "underscore"], xblock);
    }

}