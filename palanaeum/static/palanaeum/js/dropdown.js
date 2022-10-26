"use strict";

$(document).ready(function() {
    $(document).click(function () {
        $('.w3-dropdown-click > .w3-dropdown-content').removeClass('w3-show');
    });

    $('.w3-dropdown-click').click(function (event) {
        $(this).children('.w3-dropdown-content').toggleClass('w3-show');
        event.stopPropagation()
    });
});
