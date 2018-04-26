function mini_player_clicked() {
    var button = $(this);
    var audio_player = button.siblings('audio');

    if (audio_player.prop('paused')) {
        audio_player.trigger('play');
        button.removeClass('fa-play').addClass('fa-pause');
    } else {
        audio_player.trigger('pause');
        button.removeClass('fa-pause').addClass('fa-play');
    }
    audio_player.on("ended", function(){
        button.removeClass('fa-pause').addClass('fa-play');
        audio_player.prop("currentTime", 0);
    });
    return false;
}

$(function(){
    $('.mini-player').find('button').click(mini_player_clicked);
});