function showTab(tab_id) {
    let tab_nav = $('#tab-nav');
    $('.tab').hide();
    $('#' + tab_id).show();
    tab_nav.find('a').removeClass('w3-theme-action');
    tab_nav.find('a[data-tab-name="' + tab_id + '"]').addClass('w3-theme-action');
}
$(function(){
    $('#tab-nav').find('a').click(function(){
        let tab_name = $(this).data('tab-name');
        showTab(tab_name);
    })
});