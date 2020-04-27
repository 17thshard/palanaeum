"use strict";

function check_url_text() {
    const url_input = $(this);
    const text_input = url_input.closest("tr").find("input[type=text]").first();

    $.get(Palanaeum.GET_URL_TEXT, {"url": url_input.val()}, function (ret) {
        if (ret && ret.text) {
            text_input.val(ret.text);
        }
    });
}

function EntryEditor(container) {
    const self = this;
    this.container = $(container);
    this.lines_container = this.container.find(".lines");
    this.entry_id = this.container.data("entry-id");
    this.line_template = $(this.container.find(".line-template"));
    this.source_table = $(this.container.find("table.url-sources-edit-table"));
    this.source_template = $(this.container.find(".url-sources-edit-table-row-template"));
    this.add_line_button = this.container.find("button.add-line");
    this.save_button = this.container.find("#save-button");
    this.save_and_add_button = this.container.find("#save-and-add-button");
    this.add_source_button = this.container.find("button#add-url-source");
    this.direct_entry = this.container.find("input#direct");
    this.reported_by = $(this.container.find("input#reported_by"));
    this.paraphrased = $(this.container.find('input#paraphrased'));
    this.tag_input = this.container.find("#tags");
    this.date_input = this.container.find('#date');

    this.add_line_button.click(function () {
        self.add_line(self);
    });
    this.add_source_button.click(function () {
        self.add_source(self);
    });
    this.save_button.click(function() {
        self.save_button.data('last-clicked', 1);
        self.save_and_add_button.data('last-clicked', 0);
    });
    this.save_and_add_button.click(function() {
        self.save_button.data('last-clicked', 0);
        self.save_and_add_button.data('last-clicked', 1);
    });
    this.container.on("submit", function () {
        self.save_entry(self);
        return false;
    });
    this.direct_entry.on("change", function(){
       if (self.direct_entry.is(":checked")) {
           self.reported_by.parent().css('visibility', 'visible');
           self.reported_by.val(Palanaeum.USER_NAME);
           self.paraphrased.prop('checked', 'checked');
       } else {
           self.reported_by.val('');
           self.reported_by.parent().css('visibility', 'hidden');
       }
    });
    this.paraphrased.on("change", function(){
        if (self.direct_entry.is(":checked") && !self.paraphrased.is(":checked")){
            self.paraphrased.prop("checked", "checked");
        }
    });
    this.source_table.find(".url-sources-edit-table-row input[type=url]").change(check_url_text);
    attach_unsaved_warning();
    this.tinymce_config = {
        statusbar: false,
        menubar: false,
        plugins: "link nonbreaking paste searchreplace autoresize",
        toolbar: "undo redo | bold italic underline strikethrough | superscript subscript | removeformat | link nonbreaking searchreplace",
        autoresize_bottom_margin: 5,
        browser_spellcheck: true,
        setup: function(editor) {
            editor.on('keydown', function (event) {
                $('audio', parent.document).each(function() {
                    audio_control(this, event)
                });
            });
        }
    };
    tinymce.init($.extend(this.tinymce_config, {selector: ".entry-edit-table .lines textarea"}));
    tinymce.init($.extend(this.tinymce_config, {selector: "#note"}));

    $('#' + buildStringLineId(0, "speaker")).focus();
}

function buildStringLineId(idNum, suffix) {
    /// <summary>Build up the unique identifier for a given line in the Speaker/Line template</summary>
    const linePrefix = "line-";
    return linePrefix + idNum + "-" + suffix;
}

EntryEditor.prototype = {
    constructor: EntryEditor,
    add_line: function(self) {
        let new_line = self.line_template.clone();
        const line_id = self.lines_container.find("tr").length / 2;
        const speaker_id = buildStringLineId(line_id, "speaker");
        const text_id = buildStringLineId(line_id, "text");
        const order_id = buildStringLineId(line_id, "order");
        const id_id = buildStringLineId(line_id, "id");
        new_line.find(".speaker").attr("data-line-id", line_id);
        new_line.find(".speaker label").prop("for", speaker_id);
        new_line.find(".speaker input[type='text']").prop("id", speaker_id).prop("name", speaker_id);
        new_line.find(".speaker input[type='hidden'][name='order']").prop("id", order_id).prop("name", order_id).val(line_id);
        new_line.find(".speaker input[type='hidden'][name='id']").prop("id", id_id).prop("name", id_id).val("");
        new_line.find(".text").attr("data-line-id", line_id);
        new_line.find(".text label").prop("for", text_id);
        new_line.find(".text textarea").prop("id", text_id).prop("name", text_id);
        self.lines_container.append(new_line.html());
        attach_unsaved_warning();
        tinymce.init($.extend(self.tinymce_config, { selector: "#" + text_id }));

        $('#' + speaker_id).focus(); //Focus on Speaker field
        $('#' + text_id).each(function() {
            $(this).animate({ scrollTop: $(this).prop("scrollHeight") }, 1000);
        }); //Scroll down to new field over 1s

        return false;
    },
    add_source: function(self) {
        let new_row = self.source_template.clone();
        const source_id = self.source_table.find("tr.url-sources-edit-table-row").length;
        const name_id = "url-source-" + source_id + "-name";
        const url_id = "url-source-" + source_id + "-url";
        new_row.removeClass("url-sources-edit-table-row-template");
        new_row.addClass("url-sources-edit-table-row");
        new_row.find("input[type='text']").prop("name", name_id).val("");
        new_row.find("input[type='url']").prop("name", url_id).val("");
        self.source_table.find("tbody").append(new_row);
        attach_unsaved_warning();
        this.source_table.find(".url-sources-edit-table-row input[type=url]").change(check_url_text);
        return false;
    },
    save_entry: function(self) {
        tinymce.triggerSave();
        let data = {"entry_id": self.entry_id, "date": self.date_input.val()};
        const form_data = self.container.serializeArray();
        $.each(form_data, function(i, elem) {
            data[elem.name] = elem.value;
        });
        data['tags'] = self.tag_input.val();
        $.post(Palanaeum.ENTRY_SAVE, data, function(ret){
            if (ret.success) {
                let db_id;
                for (let local_id in ret["lines_id_mapping"]) {
                    if (ret["lines_id_mapping"].hasOwnProperty(local_id)) {
                        db_id = ret["lines_id_mapping"][local_id];
                        self.container.find("[data-line-id='" + local_id + "']").data("line-id", db_id);
                        self.container.find("[name='line-" + local_id + "-id']").val(db_id);
                    }
                }
                $.each(self.source_table.find(".url-sources-edit-table-row"), function (i, elem) {
                    elem = $(elem);
                    if (elem.find("input[type='text']").val() === "" && elem.find("input[type='url']").val() === "") {
                        elem.remove();
                    }
                });
                self.add_source(self);
                self.container.data("entry-id", ret["entry_id"]);
                self.entry_id = ret["entry_id"];
                for (let i = 0; i < ret["deleted_lines"].length; i++) {
                    self.container.find("[data-line-id=" + ret["deleted_lines"][i] + "]").fadeOut(1000, function () {
                        $(this).remove();
                    });
                }
                noty({"type": "success", "text": gettext("Entry successfully saved.")});
                window.unsaved_changes = false;
                window.setTimeout(function(){
                    if (self.save_and_add_button.data('last-clicked') === 1) {
                        window.location = ret['add_entry_url'];
                    }
                }, 500);
            } else {
                alert(ret["reason"]);
            }
        });
        return false;
    }
};
