$(function(){
    "use strict";
    $('.tag-selector').select2({
        minimumInputLength: 2,
        theme: "classic",
        ajax: {
            url: Palanaeum.TAGS_URL,
            dataType: 'json',
            delay: 250,
            data: function (params) {
              return {
                q: params.term, // search term
              };
            },
            // results: function(data) {
            //
            // },
            cache: true
        }
    });
});