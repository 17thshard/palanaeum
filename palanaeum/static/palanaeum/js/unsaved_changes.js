window.unsaved_changes = false;

function check_for_unsaved_changes() {
    if (window.unsaved_changes) {
        return gettext("There are some unsaved changes on this page. Are you sure you want to leave?");
    }
}

function attach_unsaved_warning() {
    $('.unsaved_warning').change(function () {
        window.unsaved_changes = true;
    }).on('input', function () {
        window.unsaved_changes = true;
    });
}

$(function () {
    $(window).bind('beforeunload', check_for_unsaved_changes);
    attach_unsaved_warning();
});