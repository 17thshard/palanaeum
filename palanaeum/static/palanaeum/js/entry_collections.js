function add_rem_entry_to_collection() {
    const self = $(this);
    const entry_id = self.data('entry-id');
    const collection_id = self.data('collection-id');
    const add = self.is(':checked');

    $.post(Palanaeum.COLLECTION_ADD_REM_URL,
        {'entry_id': entry_id, 'collection_id': collection_id, 'action': add ? 'add' : 'remove'},
        function(ret) {
            self.next('span').text(`${ret['name']} (${ret['size']})`);
        }
    );
}

function add_new_collection_confirm() {
    const add_button = $('#add-collection-button');
    const input_section = $('#add-collection-input');
    const collections_dialog = $('#collections-dialog');
    const entry_id = collections_dialog.data('entry-id');

    const collection_name = input_section.find('input').val();

    $.post(Palanaeum.COLLECTION_CREATE_URL, {'name': collection_name, 'entry_id': entry_id},
        function() {
            collections_dialog.dialog("close");
            input_section.hide();
            input_section.find('input').val('');
            add_button.show();
            $(`#e${entry_id}`).find('.collection-button').click();
        });
}

function add_new_collection() {
    // let collection_name = prompt('How do you want to name your new collection?' +
    //     '\n\r(It will be created as private)');
    const add_button = $('#add-collection-button');
    const input_section = $('#add-collection-input');
    add_button.fadeOut(200, function(){
        input_section.fadeIn(200);
    });


    if (!collection_name) return;
    const collections_dialog = $('#collections-dialog');
    const entry_id = collections_dialog.data('entry-id');

    $.post(Palanaeum.COLLECTION_CREATE_URL, {'name': collection_name, 'entry_id': entry_id},
        function() {
            collections_dialog.dialog("close");
            $(`#e${entry_id}`).find('.collection-button').click();
        });
}

function update_collection_dialog_and_display(collections_list, parent_button) {
    const list = collections_list['list'];
    const collections_dialog = $('#collections-dialog');
    const coll_list = $('#collections-scroll-list');
    const template = $('#collection-template');
    const entry_id = collections_dialog.data('entry-id');
    coll_list.find('.collection-elem').remove();

    for (const coll of list) {
        const name = coll['name'];
        const id = coll['id'];
        const checked = coll['has_entry'];
        const size = coll['size'];
        const pub = coll['public'];
        let copy = template.clone();
        copy.find('label span').text(`${name} (${size})`);
        copy.find('span.collection-elem-symbol').addClass(pub ? 'fa-globe' : 'fa-lock');
        let input = copy.find('input');
        input.prop('value', id);
        input.prop('checked', checked);
        input.data('entry-id', entry_id);
        input.data('collection-id', id);
        input.change(add_rem_entry_to_collection);

        copy.show();
        coll_list.append(copy);
    }

    // Displays a list of collections with checkboxes
    collections_dialog.dialog({
        position: { my: "right top", at: "right bottom", of: parent_button, collision: 'fit'},
        resizable: false,
        modal: true,
        width: 350,
        open: function(event, ui) {
            $('.ui-widget-overlay').bind('click', function() {
                collections_dialog.dialog('close');
            });
        }
    });
}

function collection_button_click(event) {
    const self = $(this);
    const collections_dialog = $('#collections-dialog');
    collections_dialog.data('entry-id', $(this).data('entry-id'));
    // Get the list of collection
    $.get(Palanaeum.COLLECTION_LIST_URL, {'entry_id': $(this).data('entry-id')},
        function(ret) {update_collection_dialog_and_display(ret, self)}
    );

    event.preventDefault();
    return false;
}

$(function(){
    $('a.collection-button').click(collection_button_click);
    $('#add-collection-button').click(add_new_collection);
    $('#add-collection-input input').keypress(function(event) {
        if (event.keyCode === 13) {
            add_new_collection_confirm();
        }
    });
    $('#add-collection-input button').click(add_new_collection_confirm);
});