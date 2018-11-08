"use strict";

function audio_control(player, event) {
    let scale = player.playbackRate / player.defaultPlaybackRate;

    // Function keys are 111 + ID (i.e. F3 is 114)
    switch (event.which) {
        case 118: // F7, jump back
            player.currentTime -= 5 * scale;
            break;
        case 119: // F8, play/pause
            if (player.paused)
                player.play();
            else
                player.pause();
            break;
        case 120: // F9, jump forward
            player.currentTime += 5 * scale;
            break;
        case 121: // F10, mute
            player.muted = !player.muted;
            break;
        case 122: // F11, volume down
            if (player.muted)
                player.muted = false;
            player.volume = Math.min(Math.max(player.volume - 0.1, 0), 1);
            break;
        case 123: // F12, volume up
            if (player.muted)
                player.muted = false;
            player.volume = Math.min(Math.max(player.volume + 0.1, 0), 1);
            break;
    }
}

$(document).keydown(function (event) {
    $('audio', parent.document).each(function () {
        audio_control(this, event)
    });
});

$(document).ready(function() {
    $(".playback-speed[speed='1.0']").addClass('w3-blue w3-hover-blue-gray selected');
    $('.playback-speed').click(function (event) {
        if (!$(this).hasClass('selected')) {
            let speed = $(this).data('speed');
            $(this).siblings('.playback-speed').removeClass('w3-blue w3-hover-blue-gray selected');
            $(this).addClass('w3-blue w3-hover-blue-gray selected');

            let idRef = $(this).parents(".playback-speed-container").data("audio-id");
            $("#" + idRef).each(function () {
                this.playbackRate = this.defaultPlaybackRate * speed;
            });
        }

        event.stopPropagation();
    });

    $(document).click(function () {
        $('.w3-dropdown-click > .w3-dropdown-content').removeClass('w3-show');
    });

    $('.w3-dropdown-click').click(function (event) {
        $(this).children('.w3-dropdown-content').toggleClass('w3-show');
        event.stopPropagation()
    });
});
