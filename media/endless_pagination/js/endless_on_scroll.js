(function($) {
    $(document).ready(function(){
        console.log('scrolling setup')
       $('#page_body_container').scroll(function(){
            console.log('scrolling')
            if ($(window).scrollTop() > $(document).height() - ($(window).height()*3)) {
                // temporarily unhook the scroll event watcher so we don't call a bunch of times in a row
                $(window).unbind();
                // execute the load function below that will visit the JSON feed and stuff data into the HTML
               if ($('a.endless_more').length == 1) {
                    $("a.endless_more").click();
                }
            }
        })


           //if ($('#page_body_container').scrollTop() == $(document).height() - $('#page_body_container').height() - $('#topheader').height() - $('#player').height() ) {
               //$("a.endless_more").click();
           //} 
        //});
    });
})(jQuery);
