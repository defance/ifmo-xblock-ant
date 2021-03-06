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
            get_state: runtime.handlerUrl(element, 'get_user_data'),
            reset_state: runtime.handlerUrl(element, 'reset_user_data'),
            get_current_state: runtime.handlerUrl(element, 'get_current_user_data'),
            check_no_auth: runtime.handlerUrl(element, 'check_lab_external', '', '', true),
            get_tasks_data: runtime.handlerUrl(element, 'get_tasks_data')
        };

        var id = $(element).data('id');

        var get_template = function(tmpl){
            return _.template($(element).find(tmpl).text());
        };

        var template = {
            main: get_template('#template-ant-block')
        };

        function disable_controllers(context)
        {
            $(context).find("input").addClass('disabled').attr("disabled", "disabled");
        }
        
        function enable_controllers(context)
        {
            $(context).find("input").removeClass('disabled').removeAttr("disabled");
        }

        function render(data) {
            $(element).find('.ant-content').html(template.main(data));
            render_bind();
        }
                    
        var deplainify = function(obj) {
            for (var key in obj) {
                try {
                    if (obj.hasOwnProperty(key)) {
                        obj[key] = deplainify(JSON.parse(obj[key]));
                    }
                } catch (e) {
                    console.log('failed to deplainify', obj);
                }
            }
            return obj;
        };

        function render_bind() {

            /*
             * Start lab handler.
             */
            $(element).find('.ant-start-lab').off('click').on('click', function(e) {
                $('.xblock-ant-success').removeClass('hidden');
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

            $(element).find('.ant-check-lab').off('click').on('click', function(e) {
                disable_controllers(element);
                $.ajax({ url: urls.check, type: "POST", data: '{}', success: function(data){}});
                $(this).val($(this).data('checking'));
                setTimeout($.proxy(function(){
                    $.ajax({
                        url: urls.get_current_state,
                        type: "POST",
                        data: '{}',
                        success: function(data){
                            render(JSON.parse(data.student_state));
                        },
                        complete: function(data){
                            console.info('ant-check-lab', data);
                            enable_controllers(element);
                        }
                    });
                }, this), 3000);
            });

            $(element).find('.staff-get-state-btn').off('click').on('click', function(e) {
                disable_controllers(element);
                var data = {
                    'user_login': $(element).find('input[name="user"]').val()
                };
                $.ajax({
                    url: urls.get_state,
                    type: "POST",
                    data: JSON.stringify(data),
                    success: function(data){
                        var state = deplainify(data);
                        $(element).find('.staff-info-container').html('<pre>' + JSON.stringify(state, null, '  ') + '</pre>');
                    },
                    complete: function(data) {
                        console.info('staff-get-state-btn', data);
                        enable_controllers(element);
                    }
                });
            });

            $(element).find('.staff-reset-state-btn').off('click').on('click', function(e) {
                if (!confirm('Do you really want to reset state?')) {
                    return;
                }
                disable_controllers(element);
                var data = {
                    'user_login': $(element).find('input[name="user"]').val()
                };
                $.ajax({
                    url: urls.reset_state,
                    type: "POST",
                    data: JSON.stringify(data),
                    success: function(data) {
                        var state = deplainify(data);
                        $(element).find('.staff-info-container').html('<pre>' + JSON.stringify(state, null, '  ') + '</pre>');
                    },
                    complete: function(data){
                        console.info('staff-reset-state-btn', data);
                        enable_controllers(element);

                }});
            });

            $(element).find('.staff-update-state-btn').off('click').on('click', function(e) {
                disable_controllers(element);
                var data = {
                    'user_login': $(element).find('input[name="user"]').val()
                };
                $.ajax({
                    url: urls.check,
                    type: "POST",
                    data: JSON.stringify(data),
                    success: function(data) {
                        var state = deplainify(data);
                        $(element).find('.staff-info-container').html('<pre>' + JSON.stringify(state, null, '  ') + '</pre>');
                    },
                    complete: function(data) {
                        console.info('staff-update-state-btn', data);
                        enable_controllers(element);
                    }
                });
            });
        }

        $(function($) { // onLoad

            var block = $(element).find(".ant-block");
            var state = block.attr("data-student-state");

            var is_staff = block.attr("data-is-staff") == "True";
            if (is_staff) {
                $(element).find('.instructor-info-action').leanModal();
                $(element).find('.staff-info-external-check').text(block.data('url-check-no-auth'));
                $(element).find('.staff-info-tasks-data').text(block.data('url-tasks-data'));
                $(element).find('.staff-info-grades-data').text(block.data('url-grades-data'));
            }

            var data = JSON.parse(state);
            data.urls = urls;
            render(data);

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
