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
        $.getScript(STATIC_URL + "tipTip/jquery.tipTip.minified.js", function() {
            $('.tiptip').tipTip();
        });

        // one time slots
        ui.setupLinks();
        // slots to execute at each update
        $(document).bind('signalPageUpdate', function() {
            if (document.getElementById('page_title')) {
                document.title = $('#page_title').html();
            }

            var right = $('#page_body_right');
            if (right != undefined) {
                if(!right.html().trim()) {
                    right.hide();
                } else {
                    right.show();
                }
            }
        });
        $(document).bind('signalPageUpdate', ui.setupForms);
        $(document).bind('signalPageUpdate', ui.setupPagination);
        $(document).bind('signalPageUpdate', ui.setupAutocomplete);
        
        $(document).bind('signalPlaylistTrackModificationRequest', function(e, track, playlist, action) {
            /* read playlist_track_modify first */
            var data = [playlist_track_modify, '?'];
            
            if (track.pk != undefined) {
                data.push('&track_pk='+track.pk);
            }
            else if (track.name != undefined) {
                data.push('&track_name='+encodeURIComponent(track.name));
            }
            
            if (track.artist != undefined && track.artist.name != undefined) {
                data.push('&artist_name=' + encodeURIComponent(track.artist.name));
            }

            if (playlist.pk != undefined) {
                data.push('&playlist_pk=' + playlist.pk);
            }
            else if (playlist.name != undefined) {
                data.push('&playlist_name=' + encodeURIComponent(playlist.name));
            }

            if (action != undefined) {
                data.push('&action=' + action);
            }
        
            var url = data.join('');
            $.history.load(url);
        });

        this.ready = true;
    },
    'setupLinks': function() {
        if (!ui.settings['ajaxEnable']) {
            return undefined;
        }

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
                        $('#page_body_wrapper').html(html);
                        $(document).trigger('signalPageUpdate', [url]);
                        $('#ajaxload').fadeOut();
                    },
                    beforeSend: ui.beforeSend,
                    error: ui.error,
                });
            });
        }
    },
    'setupPagination': function() {
        if (ui.settings['ajaxEnable'] && $('div.pagination').length) {
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
        if (textStatus == 'error') {
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
                        $('#page_body_wrapper').html(html);
                        ui.currentUrl = hash;
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
