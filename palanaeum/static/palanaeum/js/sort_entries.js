
function save_order(event) {
    let ordering = {};
    let eventId = $('#eventArticle').data('eventId');
    $.each($('.entry-article'), function(i, elem) {
        $(elem).data('order', i);
        ordering[$(elem).data('entryId')] = i;
    });
    $.post(
        Palanaeum.SORT_ENTRIES,
        {'ordering': JSON.stringify(ordering), 'eventId': eventId},
        function(ret){
            if (ret['success']) {
                noty({"type": "success", "text": gettext("Entries successfully reordered.")});
                window.location.assign(ret['url']);
            } else {
                noty({"type": "error", "text": gettext("Couldn't save changes.")});
            }
        });
    event.preventDefault();
    return false;
}

$( function() {
    $( "#entries" ).sortable({
      placeholder: "sortable-placeholder"
    }).disableSelection();
    $('.order-save-btn').click(save_order);
} );