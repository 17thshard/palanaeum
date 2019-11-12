function mini_player_clicked() {
    var button = $(this);
    var audio_player = button.siblings('audio');

    if (audio_player.prop('paused')) {
        var article = button.parents('#entries')
        var other_players = article.find('audio')
        other_players.each(mini_player_pause)
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

function mini_player_pause() {
    var player = $(this)
    var button = player.siblings('button')
    player.trigger('pause')
    button.removeClass('fa-pause').addClass('fa-play')

}

$(function(){
    $('.mini-player').find('button').click(mini_player_clicked);
});