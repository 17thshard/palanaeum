function showTab(tab_id) {
    let tab_nav = $('#tab-nav');
    $('.tab').hide();
    $('#' + tab_id).show();
    tab_nav.find('a').removeClass('w3-theme-action');
    tab_nav.find('a[data-tab-name="' + tab_id + '"]').addClass('w3-theme-action');
    window.location.hash = tab_id;
}
$(function(){
    $('#tab-nav').find('a').click(function(){
        let tab_name = $(this).data('tab-name');
        showTab(tab_name);
    })


    const tab_names = $('#tab-nav').find('a').map(function (tab) {
      return $(this).data('tab-name')
    } ).get();

    const hash = window.location.hash.substring(1);

    if (tab_names.indexOf(hash) !== -1) {
      showTab(hash)
    }
});