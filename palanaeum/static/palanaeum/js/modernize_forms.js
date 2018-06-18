const TIME_FORMAT = /^(\d\d:)?\d?\d:\d?\d$/;

function format_seconds(seconds) {
    let h = Math.floor(seconds / 60 / 60);
    let m = Math.floor(seconds / 60 % 60);
    let s = Math.floor(seconds % 60);

    if (h > 9) { h = '' + h } else { h = '0' + h }
    if (m > 9) { m = '' + m } else { m = '0' + m }
    if (s > 9) { s = '' + s } else { s = '0' + s }

    if (h !== '00') {
        return h + ':' + m + ':' + s;
    } else {
        return m + ':' + s;
    }
}

function seconds_from_formated(formated) {
    if (!TIME_FORMAT.test(formated)) {
        throw "Invalid format: " + formated;
    }
    const parts = formated.split(':');
    if (parts.length === 2) {
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }
    if (parts.length === 3) {
        return parseInt(parts[0]) * 60 * 60 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
    }
    throw "Invalid format";
}

function check_duration_format(text) {
    if (!TIME_FORMAT.test(text)) {
        return false;
    }
    const parts = text.split(':');
    if (parts.length === 3) {
        if (parseInt(parts[1]) >= 60) {
            return false;
        }
        if (parseInt(parts[2]) >= 60) {
            return false;
        }
    }
    if (parts.length === 2) {
        if (parseInt(parts[0]) >= 60) {
            return false;
        }
        if (parseInt(parts[1]) >= 60) {
            return false;
        }
    }
    return true;
}

let duration_input_template = '\
    <div class="duration-input-div">\
        <button class="w3-tag w3-theme" type="button" data-action="minus">-</button>\
        <input type="text" class="duration-input" value="">\
        <button class="w3-tag w3-theme" type="button" data-action="plus">+</button>\
    </div>';

function create_duration_input_div() {
    return $(duration_input_template);
}

function init_duration_input_div(duration_input_div, readonly) {
    const div = $(duration_input_div);

    let input, minus, plus;
    input = $(div).find('input.duration-input');
    minus = $(div).find('.minus');
    plus = $(div).find('.plus');

    if (readonly) {
        minus.css('visibility', 'hidden');
        plus.css('visibility', 'hidden');
        input.attr('readonly', 'readonly');
        return;
    }

    input.focusin(function () {
        $(this).data('old-val', $(this).val());
    }).focusout(function () {
        const nval = $(this).val();
        let seconds;
        if (!check_duration_format(nval)) {
            $(this).val($(this).data('old-val'));
            return;
        }
        try {
            seconds = seconds_from_formated(nval);
        } catch (err) {
            $(this).val($(this).data('old-val'));
            return;
        }
        if ($(this).data('max-val') && $(this).data('max-val') < seconds) {
            seconds = $(this).data('max-val');
        }
        $(this).val(format_seconds(seconds));
    });

    minus.click(function () {
        const input = $(this).siblings('.duration-input');
        let seconds;
        try {
            seconds = seconds_from_formated(input.val());
        } catch (err) {
            alert(err);
        }
        seconds -= 1;
        if (seconds < 0) seconds = 0;
        if (input.data('max-val') && input.data('max-val') < seconds) {
            seconds = input.data('max-val');
        }
        input.val(format_seconds(seconds)).trigger('change');
    });

    plus.click(function () {
        const input = $(this).siblings('.duration-input');
        let seconds;
        try {
            seconds = seconds_from_formated(input.val());
        } catch (err) {
            alert(err);
        }
        seconds += 1;
        if (input.data('max-val') && input.data('max-val') < seconds) {
            seconds = input.data('max-val');
        }
        input.val(format_seconds(seconds)).trigger('change');
    });

    //We took +/- out of the tab order, so provide shortcuts
    div.on("keyup", function (event) {
        if (!event.altKey) {
            return true;
        }
        switch (event.which) {
            case 107: // +
            case 187: // = (the +/= key)
                plus.click();
                input.focus();
                break;
            case 109: // -
            case 189: // - (hyphen)
                minus.click();
                input.focus();
                break;
            default:
                return true;
        }
        event.preventDefault();
        return false;
    });
}

function add_http_to_start() {
    let val = $(this).val();
    if (val.length === 0)
        return;
    if (!/^(http:\/\/|https:\/\/|ftp:\/\/)/.test(val)) {
        val = 'http://' + val;
    }
    $(this).val(val);
}

$(function(){
    if (!Modernizr.inputtypes.date) {
        const date_inputs = $('input[type="date"]');
        if (Modernizr.placeholder) {
            date_inputs.attr('placeholder', 'YYYY-MM-DD');
        } else {
            date_inputs.after("<br/><small>" + getText("Required format: YYYY-MM-DD") + "</small>")
        }
        date_inputs.datepicker({ dateFormat: 'yy-mm-dd' });
    }
    $('input[type="url"]').focusout(add_http_to_start);
    $('.duration-input-div').each(function() {init_duration_input_div(this)});
    $('select.select2').select2({
        'minimumResultsForSearch': 10,
    });
    tinymce.init({
        statusbar: false,
        menubar: false,
        plugins: "link nonbreaking paste searchreplace autoresize",
        toolbar: "undo redo | bold italic underline strikethrough | superscript subscript | removeformat | link nonbreaking searchreplace",
        autoresize_bottom_margin: 5,
        browser_spellcheck: true,
        selector: ".tinymce-enabled textarea"
    });
});