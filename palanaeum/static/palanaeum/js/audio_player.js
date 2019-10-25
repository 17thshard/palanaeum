"use strict";

function AudioPlayer(player) {
    this.snippets = [];
    this.snippet_playing = null;
    this.player_container = $(player);

    this.player = this.player_container.find('audio').first();
    this.progress_bar = this.player_container.find('#progress');
    this.progress_past = this.progress_bar.find('#past');
    this.time_indicator = this.progress_bar.find('#time-indicator');

    this.fast_back_button = this.player_container.find('#fastbackward');
    this.back_button = this.player_container.find('#backward');
    this.play_button = this.player_container.find('#play');
    this.forward_button = this.player_container.find('#forward');
    this.fast_forward_button = this.player_container.find('#fastforward');
    this.add_snippet_button = this.player_container.find('#add-snippet');
    this.extend_snippet_button = this.player_container.find('#extend-snippet');
    const self = this;
    this.fast_back_button.click(function () { self.modify_play_time(-60);});
    this.back_button.click(function () { self.modify_play_time(-5);});
    this.play_button.click(function () { self.play_pause();});
    this.forward_button.click(function () { self.modify_play_time(5);});
    this.fast_forward_button.click(function () { self.modify_play_time(60);});
    this.progress_bar.click(function (event) { self.progress_clicked(event);});

    this.readonly_mode = !STAFF_USER;

    if (this.add_snippet_button)
        this.add_snippet_button.click(function () { self.create_snippet();});
    if (this.extend_snippet_button)
        this.extend_snippet_button.click(function() { self.extend_last_snippet();});


    $('.save').click(function () { self.save_snippets(self);});
    $('#rename-source').click(function () { self.rename_source(self, $('#source-title').val());});

    this.player.on('timeupdate', self.track_play_progress);
    this.player.on('ended', function() {
        self.play_button.removeClass('fa-pause').addClass('fa-play');
        self.set_current_time(0);
    });

    $(window).on('keypress', function(event){
        if ($(document.activeElement).prop('tagName') === 'INPUT') {
            return true;
        }
        switch (event.which) {
            case 100: // d
            case 68:  // D
                self.fast_back_button.click();
                break;
            case 102: // f
            case 70:  // F
                self.back_button.click();
                break;
            case 103: // g
            case 71:  // G
                self.play_button.click();
                break;
            case 104: // h
            case 72:  // H
                self.forward_button.click();
                break;
            case 106: // j
            case 74:  // J
                self.fast_forward_button.click();
                break;
            case 32: // SPACE
                if (!self.readonly_mode) {
                    if (event.shiftKey)
                        self.extend_last_snippet();
                    else
                        self.create_snippet();
                }
                break;
            default:
                return true;
        }
        event.preventDefault();
        return false;
    });
}

AudioPlayer.get_instance = function() {
    if (AudioPlayer.instance)
        return AudioPlayer.instance;
    AudioPlayer.instance = new AudioPlayer($('#player'));
    return AudioPlayer.instance;
};

AudioPlayer.prototype = {
    constructor: AudioPlayer,
    instance: null,
    get_source_id: function() {
        const self = AudioPlayer.get_instance();
        return self.player.data('source-id');
    },
    get_duration: function() {
        const self = AudioPlayer.get_instance();
        let duration = parseFloat(self.player.prop('duration'));
        if (isNaN(duration)) {
            duration = parseFloat(self.player.data('duration'));
        }
        return duration;
    },
    get_current_time: function() {
        const self = AudioPlayer.get_instance();
        return parseFloat(self.player.prop("currentTime"));
    },
    set_current_time: function(time) {
        const self = AudioPlayer.get_instance();
        time = Math.floor(time);
        self.player.prop("currentTime", time);
    },
    rename_source: function(self, new_name) {
        if (self.readonly_mode) return;
        $.post(Palanaeum.SNIPPET_RENAME_URL, {'source_id': self.get_source_id(), 'title': new_name}, function() {
            $('h1').text(new_name);
            noty({ 'text': 'New title saved.', 'type': 'success' });
        });
    },
    play_pause: function() {
        const self = AudioPlayer.get_instance();
        if (self.player.prop('paused')) {
            self.player.trigger('play');
            self.play_button.removeClass('fa-play').addClass('fa-pause');
        } else {
            self.player.trigger('pause');
            self.play_button.removeClass('fa-pause').addClass('fa-play');
        }
    },
    modify_play_time: function(modifier) {
        const self = AudioPlayer.get_instance();
        self.set_current_time(self.get_current_time() + modifier);
    },
    track_play_progress: function() {
        const self = AudioPlayer.get_instance();
        const total_time = self.get_duration();
        const current_time = self.get_current_time();

        self.time_indicator.text(format_seconds(Math.floor(current_time)) + " / " + format_seconds(Math.floor(total_time)));
        if (self.snippet_playing) {
            self.time_indicator.html(self.time_indicator.text() + "<br/>Locked to snippet.<br/>" +
                "<small>Click on the progress bar to unlock.</small>");
        }
        self.progress_past.css('width', current_time / total_time * 100 + '%');

        if (self.snippet_playing) {
            const stop = self.snippet_playing.end_time;
            if (current_time >= stop) {
                self.play_pause();
                self.set_current_time(self.snippet_playing.start_time);
            }
        }
    },
    progress_clicked: function(event) {
        const self = AudioPlayer.get_instance();
        const total_width = self.progress_bar.width();
        const click_position = event.pageX - self.progress_bar.offset().left;
        const track_time = self.get_duration();
        const new_time = track_time * (click_position / total_width);
        self.snippet_playing = null;
        self.set_current_time(new_time);
    },
    create_snippet: function() {
        const self = AudioPlayer.get_instance();
        if (self.readonly_mode) return;
        const time = Math.floor(self.get_current_time());
        for (let i=0; i<self.snippets.length; i++) {
            if (self.snippets[i].start_time === time) {
                return;
            }
        }
        const snippet = new Snippet(time, Math.min(time + 10, self.get_duration()));
        $.post(Palanaeum.SNIPPET_CREATE_URL, {'source_id': self.get_source_id()}, function(ret){
            if (ret['success']) {
                window.unsaved_changes = true;
                snippet.db_id = ret['snippet_id'];
                snippet.saved = false;
                $('.save').show();
                self.append_snippet(snippet);
                self.draw_snippets();
                noty({text: 'Snippet created!'});
            } else {
                alert(ret['reason']);
            }
        });
    },
    extend_last_snippet: function() {
        const self = AudioPlayer.get_instance();
        if (self.readonly_mode) return;
        const time = Math.floor(self.get_current_time());
        if (self.snippets.length === 0) {
            return;
        }
        let snippet = undefined;

        //Get last snippet
        for (let snip of self.snippets) {
            if (snip.start_time > time)
                continue;
            if (snippet === undefined)
                snippet = snip;
            if (snippet.start_time < snip.start_time)
                snippet = snip;
        }

        if (snippet === undefined)
            return;

        //Extend the last snippet
        snippet.end_time = time;
        snippet.redraw();
        window.unsaved_changes = true;
        $('.save').show();
        self.draw_snippets();
    },
    append_snippet: function(snippet) {
        const self = AudioPlayer.get_instance();
        self.snippets.push(snippet);
        self.sort_snippets();
    },
    remove_snippet: function(snippet) {
        const self = AudioPlayer.get_instance();
        if (self.readonly_mode) return;
        const idx = self.snippets.indexOf(snippet);
        self.snippets.splice(idx, 1);
    },
    sort_snippets: function() {
        const self = AudioPlayer.get_instance();
        self.snippets.sort(function (left, right) {
            //Primary sort on starts, secondary on ends preferencing ending sooner
            return (left.get_start_time() - right.get_start_time()) || (left.get_end_time() - right.get_end_time());
        });
    },
    draw_snippets: function () {
        const self = AudioPlayer.get_instance();
        self.progress_bar.find('.snippet').detach();
        $('.snippet-row').detach();
        self.snippets.forEach(function(snippet) {
            const tr = snippet.draw_tableRowSnippet();
            const bp = snippet.draw_snippet_highlight();
            self.progress_bar.append(bp);
            $('#snippets-table').append(tr);
        });
    },
    save_snippets: function(self) {
        if (self.readonly_mode) return;
        const data = {'source_id': self.get_source_id()};
        $.each(self.snippets, function (i, snippet){

            data[`snippet-${snippet.db_id}-beginning`] = snippet.get_start_time();
            data[`snippet-${snippet.db_id}-length`] = snippet.get_length();
            data[`snippet-${snippet.db_id}-comment`] = snippet.comment;
            data[`snippet-${snippet.db_id}-optional`] = snippet.optional;
        });
        $.post(Palanaeum.SNIPPET_EDIT_URL, data, function(ret){
            if (ret['success']) {
                $('.save').hide();
                window.unsaved_changes = false;
                $.each(self.snippets, function (i, snippet) {
                    snippet.got_saved(snippet, ret['edit_urls'][snippet.db_id]);
                });
                noty({text: 'Snippets saved!'});
            } else {
                alert(ret['reason']);
            }
        });
    },
    play_snippet: function(self, snippet) {
        self.set_current_time(snippet.start_time);
        self.snippet_playing = snippet;
        if (self.player.prop("paused")) {
            self.play_pause();
        }
    }
};

const snippet_time_template = '\
    <div class="duration-input-div">\
        <button class="w3-tag button1 minus" type="button" data-action="minus" tabindex="-1" title="Alt-">-</button>\
        <input class="duration-input">\
        <button class="w3-tag button1 plus" type="button" data-action="plus" tabindex="-1" title="Alt+">+</button>\
    </div>\
    ';
const snippet_tr_template = '\
<tr class="snippet-row">\
    <td>\
        <span class="snippet-id"></span>\
    </td>\
    <td>\
        <button class="button1 fa fa-fw fa-play snippet-play"></button>\
    </td>\
    <td>\
        ' + snippet_time_template + '\
    </td>\
    <td>\
        ' + snippet_time_template + '\
    </td>\
    <td>\
        <input class="comment" maxlength="500">\
    </td>\
    <td>\
        <input type="checkbox" class="optional" style="min-width:50px">\
    </td>\
    <td>\
        <a href="" class="entry-anchor">\
            <button class="w3-tag button2 entry" tabindex="-1">\
                <span class="fa fa-pencil"></span>\
            </button>\
        </a>\
    </td>\
    <td>\
        <a href="#" tabindex="-1" class="w3-tag visibility-switch" data-id="" data-class="snippet"><span class="fa fa-eye-slash hide_text"></span><span class="fa fa-eye show_text"></span></span></a>\
        <button tabindex="-1" class="w3-tag w3-red delete" type="button"><span class="fa fa-trash"></span></button>\
    </td>\
</tr>\
';

function Snippet(start_time, end_time, db_id, visible, comment, entry_edit_url, has_entry, muted, optional) {
    this.start_time = start_time;
    this.end_time = end_time;
    this.db_id = db_id;
    this.saved = !!db_id;
    this.local_id = Snippet.get_next_local_id();
    this.bp_elem = null;
    this.tr_elem = null;
    this.visible = visible;
    this.comment = comment;
    this.entry_edit_url = entry_edit_url;
    this.has_entry = has_entry;
    this.muted = muted;
    this.optional = optional;
}

Snippet.local_id_counter = 0;
Snippet.get_next_local_id = function () {
    Snippet.local_id_counter += 1;
    return Snippet.local_id_counter;
};

Snippet.prototype = {
    constructor: Snippet,
    get_start_time: function() {
        return this.start_time;
    },
    get_end_time: function() {
        return this.end_time;
    },
    get_length: function() {
        return Math.floor(this.end_time - this.start_time);
    },
    redraw: function() {
        this.bp_elem = undefined;
        this.tr_elem = undefined;
    },
    draw_snippet_highlight: function() {
        const ap = AudioPlayer.get_instance();
        let bp;
        if (this.bp_elem) {
            return this.bp_elem;
        }
        bp = $('<div class="snippet">');
        bp.data('local-id', this.local_id);
        bp.data('snippet', this);
        bp.css('left', this.start_time / ap.get_duration() * 100 + '%');
        bp.css('width', this.get_length() / ap.get_duration() * 100 + '%');
        if (this.muted) {
            bp.addClass('muted');
        }
        this.bp_elem = bp;
        return bp;
    },

    draw_tableRowSnippet: function() {
        if (this.tr_elem) {
            this.tr_elem.find('.snippet-id').text(this.db_id);
            return this.tr_elem;
        }

        const ap = AudioPlayer.get_instance();
        const readonly_mode = ap.readonly_mode;
        const self = this;
        const tr = $(snippet_tr_template);
        tr.data('local-id', this.local_id);
        tr.data('snippet', this);
        tr.find('.comment').val(this.comment);
        if (this.muted) {
            tr.addClass('muted');
        }

        const onCapTimeChanged = function (event) {
            const edge_push = 10;
            if (readonly_mode) return;
            let is_start_field, dependent_input, input_field;
            let audio_duration, field_time;
            let limits, new_time;
            is_start_field = event.data.isStartField;
            dependent_input = event.data.dependentInput;
            input_field = $(this);
            audio_duration = ap.get_duration();
            try {
                field_time = seconds_from_formated(input_field.val());
            } catch (err) {
                alert(err);
                return;
            }
            try {
                limits = {
                    lower_bound: is_start_field ? 0 : 1,
                    upper_bound: is_start_field ? audio_duration - 1 : audio_duration,
                    other_field: seconds_from_formated(dependent_input.val())
                };
            } catch (err) {
                alert(err);
                return;
            }
            new_time = Math.min(Math.max(field_time, limits.lower_bound), limits.upper_bound);

           //Try to push other field away to make room if necessary
            if (is_start_field && new_time >= limits.other_field) {
                const new_end = Math.min(audio_duration, new_time + edge_push);
                dependent_input.val(format_seconds(new_end));
                self.end_time = new_end;
            }
            else if (!is_start_field && new_time <= limits.other_field) {
                const new_start = Math.max(0, new_time - edge_push);
                dependent_input.val(format_seconds(new_start));
                self.start_time = new_start;
            }

            if (new_time !== field_time) //Make field comply with value
            {
                input_field.val(format_seconds(new_time));
            }
            is_start_field ? self.start_time = new_time : self.end_time = new_time;

            self.saved = false;
            self.redraw();
            window.unsaved_changes = true;
            $('.save').show();
            ap.sort_snippets();
            ap.draw_snippets();
        };

        const setupInputDiv = function (isStartField, primaryInput, dependentInput) {
            primaryInput.val(format_seconds(isStartField ? self.start_time : self.end_time));
            primaryInput.data('max-val', ap.get_duration());
            if (!readonly_mode)
                primaryInput.change({ dependentInput: dependentInput, isStartField: isStartField }, onCapTimeChanged);
        };

        const starting_div = tr.find('.duration-input-div').first();
        const starting_input = starting_div.find('.duration-input');
        const ending_div = tr.find('.duration-input-div').last();
        const ending_input = ending_div.find('.duration-input');
        setupInputDiv(true, starting_input, ending_input);

        setupInputDiv(false, ending_input, starting_input);
        init_duration_input_div(starting_div, this.muted);

        init_duration_input_div(ending_div, this.muted);
        tr.find('.snippet-play').click(function() {

            ap.play_snippet(ap, self);
        });
        tr.find('.snippet-id').text(self.db_id);
        tr.find('.comment').on('input', function() {
            self.comment = $(this).val();
            self.saved = false;
            window.unsaved_changes = true;
            $('.save').show();
        });
        const del_button = tr.find('.delete');
        const visibility_button = tr.find('.visibility-switch');
        const entry_button = tr.find('.entry');
        const entry_anchor = tr.find('.entry-anchor');
        const optional_checkbox = tr.find('.optional').first();

        del_button.click(function () { self.delete_snippet(self);});

        optional_checkbox.prop('checked', this.optional);
        optional_checkbox.on('change', () => {
            this.optional = !this.optional;
            this.saved = false;
            window.unsaved_changes = true;
            $('.save').show();
        });

        if (this.entry_edit_url) {
            entry_anchor.prop('href', this.entry_edit_url);
        }

        if (!this.has_entry) {
            entry_button.find('span').addClass('w3-text-red');
        }

        del_button.prop('title', gettext('delete'));
        if (this.visible) {
            visibility_button.prop('title', gettext('Hide'));
            visibility_button.addClass('hide');
        } else {
            visibility_button.prop('title', gettext('Show'));
            visibility_button.addClass('show');
        }
        visibility_button.click(show_hide_object);
        visibility_button.data('id', self.db_id);
        if (!this.saved) {
            visibility_button.hide();
            entry_anchor.hide();
        }
        entry_button.prop('title', gettext('edit entry'));

        if (readonly_mode) {
            tr.find('.duration-input-div button').css('visibility', 'hidden');
            tr.find('.comment').prop('readonly', true);
            visibility_button.hide();
            del_button.hide();
            optional_checkbox.attr("disabled", true); // disable checkbox rather than hide it
        }

        this.tr_elem = tr;
        return tr;
    },

    got_saved: function (self, edit_url) {
        self.saved = true;
        const visibility_button = self.tr_elem.find('.visibility-switch');
        const edit_entry_button = self.tr_elem.find('.entry-anchor');
        visibility_button.show();
        edit_entry_button.attr("href", edit_url);
        edit_entry_button.show();
    },
    delete_snippet: function(self) {
        const ap = AudioPlayer.get_instance();
        if (ap.readonly_mode) return;
        if (!confirm(gettext("Are you sure you want to delete this snippet?"))) {
            return;
        }
        if (self.tr_elem)
            self.tr_elem.remove();
        if (self.bp_elem)
            self.bp_elem.remove();
        ap.remove_snippet(self);
        $.post(Palanaeum.SNIPPET_DELETE_URL, {'db_id': this.db_id}, function (ret) {
            if (ret['success']) {
                noty({text: gettext("Snippet deleted!"), type: 'warning'});
            } else {
                alert(ret['reason']);
            }
        });
    }
};