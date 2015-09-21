function AntXBlockEdit(runtime, element)
{

    var save = function() {
        var view = this;
        view.runtime.notify('save', {state: 'start'});
        var data = {};
        $(element).find(".input").each(function(index, input) {
            data[input.name] = input.value;
        });
        $.ajax({
            type: "POST",
            url: runtime.handlerUrl(element, 'save_settings'),
            data: JSON.stringify(data),
            success: function() {
                runtime.notify('save', {state: 'end'});
            }
        });
    };

    var ant_sync = function() {

        console.log('started sync');

        var data = {
            course_id: $(element).find(".input[name=course_id]").val(),
            unit_id: $(element).find(".input[name=unit_id]").val()
        };

        var ant_id_validator = /\d+/i;
        console.log(data.course_id);
        console.log(data.unit_id);

        if (ant_id_validator.test(data.course_id) && ant_id_validator.test(data.unit_id)) {
            $.ajax({
                type: "POST",
                url: runtime.handlerUrl(element, 'get_course_info'),
                data: JSON.stringify(data),
                complete: function() {
                },
                success: function(data) {
                    data = JSON.parse(data);
                    console.log('course_id', $(element).find(".input[name=course_id]").val(), data.course_id);
                    console.log('unit_id', $(element).find(".input[name=unit_id]").val(), data.unit_id);
                    if (data.course_id == $(element).find(".input[name=course_id]").val() && data.unit_id == $(element).find(".input[name=unit_id]").val()) {
                        $(element).find(".input[name=attempts_limit]").val(data.attempts);
                        $(element).find(".input[name=time_limit]").val(data.limit);
                        alert('Attempts and time limit synchronized.');
                    } else {
                        alert('Course id and unit id differ.');
                    }
                },
                error: function() {
                    alert('Failed to obtain ant limits for course.');
                }
            });
        } else {
            alert('Failed to validate "course_id" and "unit_id" over "/\\d+/i".');
        }

    };

    $(function(){
        // Init template
        var ant_block = $(element).find('.ant-block-editor');
        var data = ant_block.data('metadata');
        var template = _.template(ant_block.find('.ant-template-base').text());
        ant_block.find('.ant-block-content').html(template(data));

        $(element).find('.btn.ant_sync').on('click', ant_sync);
    });

    return {
        save: save
    }
}