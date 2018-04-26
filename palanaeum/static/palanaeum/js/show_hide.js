/* The element to be shown/hidden has to have data-class and data-id attributes */
function show_hide_object(event) {
    let self = $(this);
    let mode = self.hasClass('show') ? 'show' : 'hide';
    let q = '';
    if (mode === 'show')
        q = gettext("Are you sure you want to show this element to the world?");
    else
        q = gettext("Are you sure you want to hide this element from the world?");

    if (!confirm(q)) {
        event.preventDefault();
        return false;
    }

    let data = {
        'class': self.data('class'),
        'id': self.data('id'),
        'mode': mode
    };
    $.post(Palanaeum.SHOW_HIDE_URL, data, function (response) {
        if (response['success']) {
            self.toggleClass('show hide');
            self.closest('article').toggleClass('hidden-element');
            if (mode === 'show') {
                self.prop('title', gettext('Hide'));
            } else {
                self.prop('title', gettext('Show'));
            }
        } else {
            alert(response['reason']);
        }
    });
    event.preventDefault();
    return false;
}

function init_vibility_switches() {
    $('a.visibility-switch').click(show_hide_object);
}

$(function () {
    init_vibility_switches();
});
