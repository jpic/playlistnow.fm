var ui = {
    'ready': false,
    'currentRequest': false,
    'currentUrl': document.location.hash.replace(/^#/, ''),
    'settings': {
        'ajaxEnable': true,
    },
    'css': [
        STATIC_URL + "JSONSuggestBox/jsonSuggest.css",
        STATIC_URL + "local/reset.css",
        STATIC_URL + "local/screen.css",
        STATIC_URL + "local/prod.css",
        STATIC_URL + "local/tipTip.css",
    ],
    'init': function() {
        $.getScript(STATIC_URL + "swfobject/swfobject.js", function() {
            var params = { allowScriptAccess: "always" };
            var atts = { id: "myytplayer" };
            swfobject.embedSWF("http://www.youtube.com/apiplayer?enablejsapi=1&playerapiid=ytplayer", 
                               "ytapiplayer", "0", "0", "8", null, null, params, atts);
        });

        $.getScript(STATIC_URL + "tipTip/jquery.tipTip.minified.js", function() {
            $('.tiptip').tipTip();
        });

        ui.setupLinks();
        $(document).bind('signalPageUpdate', function() {
            if (document.getElementById('page_title')) {
                document.title = $('#page_title').html();
            }
        });
        $(document).bind('signalPageUpdate', ui.setupForms);
        $(document).bind('signalPageUpdate', ui.setupPagination);
        $(document).bind('signalPageUpdate', ui.setupAutocomplete);

        this.ready = true;
    },
    'setupLinks': function() {
        $('a').live('click', function(e) {
            e.preventDefault();
            var url = $(this).attr('href');
            $.history.load(url);
        });
    },
     'setupForms': function() {
        if (ui.settings['ajaxEnable'] && $('form').length) {
            $('form').submit(function(e) {
                e.preventDefault();
                var url = $(this).attr('action');
    
                $.ajax({
                    url: url,
                    dataType: 'html',
                    data: $(this).serialize(),
                    type: $(this).attr('method'),
                    success: function(html, textStatus, request) {
                        $('#ajaxload').fadeOut();
                        $('#page_body').html(html);
                        $(document).trigger('signalPageUpdate', [url]);
                    },
                    beforeSend: ui.beforeSend,
                    error: ui.error,
                });
            });
        }
    },
    'setupPagination': function() {
        if ($('div.pagination').length) {
            $('div.pagination a').each(function() {
                var href = $(this).attr('href');
                if (href.match(/^\?/)) {
                    $(this).attr('href', ui.currentUrl.replace(/\?page=.*$/, '') + href);
                }
            });
        }

    },
    'setupAutocomplete': function() {
        if ($('input#term').length == 0) {
            return true;
        }

        // we'll just use it for autoload
        function doSetupAutocomplete() {
            var autocompleteData = [];
            var autocompleteRequest;
            var autocompleteSettings = {
                minCharacters: 1,
                maxResults: undefined,
                wildCard: "",
                caseSensitive: false,
                notCharacter: "!",
                maxHeight: 350,
                highlightMatches: false,
                onSelect: function(item) {
                    $.history.load(item['url']);
                },
                ajaxResults: true,
                width: undefined
            };
            
            $('input#term').jsonSuggest(function() {
                $.ajax({
                    url: music_search_autocomplete + '?term=' + $('input#term').val(),
                    dataType: 'json',
                    success: function(data) {
                        autocompleteData = data;
                    },
                    async: false,
                });
            
                return autocompleteData;
            }, autocompleteSettings);
        }

        if ($('input#term').jsonSuggest == undefined) {
            $.getScript(STATIC_URL + 'JSONSuggestBox/jquery.jsonSuggest-dev.js', doSetupAutocomplete);
        } else {
            doSetupAutocomplete();
        }

    },
    'beforeSend': function(req) {
        var loader = $('#ajaxload');
        if (loader.css('display') == 'none') {
            loader.fadeIn();
        }
        if (ui.currentRequest) {
            ui.currentRequest.abort()
        }
        ui.currentRequest = req;
    },
    'error': function(req, textStatus) {
        $('#ajaxload').fadeOut();
        if (textStatus != 'error') {
            $('#body').html('We are sorry but your request caused a bug');
        }
        ui.currentRequest = false;
    }
}


$(document).ready(function() {
    if (ui.settings.ajaxEnable) {
        $.getScript(STATIC_URL + "jquery.history.js", function() {
            $.history.init(function(hash) {
                if (!hash) {
                    return true;
                }

                $.ajax({
                    url: hash,
                    dataType: 'html',
                    success: function(html, textStatus, request) {
                        $('#ajaxload').fadeOut();
                        $('#page_body').html(html);
                        $(document).trigger('signalPageUpdate', [hash]);
                    },
                    beforeSend: ui.beforeSend,
                    error: ui.error,
                });
    
                if (!ui.ready) {
                    ui.init();
                }
            }, { unescape: ",/?=" });
        });
    }
});
