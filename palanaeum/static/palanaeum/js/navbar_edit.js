"use strict";

function new_item(event) {
	const newRow = $(`
<tr class="navbar-item-row">
	<td><!-- Left blank for CSS row number --></td>
	<td>
		<select class="w3-select type_input">
			<option value="link" selected>Top-level link</option>
			<option value="dropdown">Dropdown</option>
			<option value="sublink">Sub-link</option>
		</select>
	</td>
	<td><input class="w3-input label_input" type="text" maxlength="32" value=""></td>
	<td><input class="w3-input icon_input" type="text" maxlength="32" value=""></td>
	<td><input class="w3-input url_input" type="text" maxlength="200" value=""></td>
	<td>
		<button class="w3-btn w3-red remove-navbar-item" title="Remove">
			<span class="fa fa-trash" aria-hidden="true"></span><span class="w3-hide-small"></span>
		</button>
	</td>
</tr>
	`).appendTo('#navbar-item-data');
	newRow.find('.remove-navbar-item').click(remove_item);
}

function remove_item(event) {
	$(event.target).parents('.navbar-item-row').remove();
}

function save_items(event) {
	const data = {};
	const kids = $('#navbar-item-data').children();
	data.count = kids.length;
	kids.each(function(i, e) {
		const type = e.querySelector('.type_input').value;
		const icon = e.querySelector('.icon_input').value;
		const label = e.querySelector('.label_input').value;
		const url = e.querySelector('.url_input').value;
		data[`${i}-type`] = type;
		data[`${i}-icon`] = icon;
		data[`${i}-label`] = label;
		data[`${i}-url`] = url;
	});
	
	$.post(Palanaeum.NAVBAR_SAVE_URL, data, function(ret){
		if (ret.success) {
			noty({
				"type": "success",
				"text": gettext("Navigation bar successfully saved. Reloading..."),
				"timeout": 500,
				"callback": {
					"afterClose": () => location.reload(),
				},
			});
		} else {
			alert(ret["reason"]);
		}
	});
}

function reset_items(event) {
	if (confirm(gettext("Are you sure you want to reset the navigation bar back to the default?"))) {
		$.post(Palanaeum.NAVBAR_RESET_URL, {}, function(ret){
			if (ret.success) {
				noty({
					"type": "success",
					"text": gettext("Navigation bar successfully reset. Reloading..."),
					"timeout": 500,
					"callback": {
						"afterClose": () => location.reload(),
					},
				});
			} else {
				alert(ret["reason"]);
			}
		});
	}
}

$('.sortable').sortable();
$('.new-navbar-item').click(new_item);
$('.remove-navbar-item').click(remove_item);
$('.save-navbar-items').click(save_items);
$('.reset-navbar-items').click(reset_items);
