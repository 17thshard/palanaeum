function open_sidenav() {
    $("#sidenav").show();
}

function close_sidenav() {
    $("#sidenav").hide();
}

function switch_mobi_search() {
    "use strict";
    var mobile_search = $('#mobile-search');
    if (mobile_search.is(':visible')) {
        mobile_search.animate({'opacity': 0}, 200, 'swing', function() {
            mobile_search.hide();
            mobile_search.animate({height: '-=10'}, 500);
        });
    } else {
        mobile_search.animate({height: '+=10'}, 200, 'swing', function() {
            mobile_search.show().animate({'opacity': '100'}, 500);
            mobile_search.find('input').focus();
        });
    }
}

//Navbar dropdowns
function dropdown(event) {
    $('#userMenu').toggleClass('w3-show');
    event.stopPropagation();
    return false;
}

//Navbar dropdowns
function dropdown2(event) {
    $('#menuSmall').toggleClass("w3-show");
    event.stopPropagation();
    return false;
}

$(function(){
    $('.close-sidenav').click(close_sidenav);
    $('.open-sidenav').click(open_sidenav);
    $('.switch-mobi-search').click(switch_mobi_search);
    $(window).scroll(function() {
        if ($(this).scrollTop() > 150) {
            $("#desktop-header-small:hidden").css('visibility','visible').fadeIn('fast');
        } else {
            $("#desktop-header-small:visible").fadeOut("fast");
        }
    });
});