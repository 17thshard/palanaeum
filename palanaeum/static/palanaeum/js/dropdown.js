"use strict";

function reset_dropdowns() {
    $('.w3-dropdown-click').removeClass('drop-open');
    $('.w3-dropdown-click > .w3-dropdown-content').removeClass('w3-show');
}
$(document).ready(function() {
    $(document).click(reset_dropdowns);
    
    $('.w3-dropdown-click').click(function (event) {
        const wasClosed = !$(this).hasClass('drop-open');
        reset_dropdowns();
        if (wasClosed) {
            $(this).addClass('drop-open');
            $(this).children('.w3-dropdown-content').addClass('w3-show');
        }
        event.stopPropagation()
    });
});
