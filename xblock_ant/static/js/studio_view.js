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
                view.runtime.notify('save', {state: 'end'});
            }
        });
    };

    $(function(){
        // Init template
        var ant_block = $(element).find('.ant-block-editor');
        var data = ant_block.data('metadata');
        var template = _.template(ant_block.find('.ant-template-base').text());
        ant_block.find('.ant-block-content').html(template(data));
    });

    return {
        save: save
    }
}