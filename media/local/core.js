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
        $.getScript(STATIC_URL + "jquery.simplemodal.min.js", function() {
        });

        // one time slots
        ui.setupLinks();
        // slots to execute at each update
        $(document).bind('signalPageUpdate', function() {
            if (document.getElementById('page_title')) {
                document.title = $('#page_title').html();
            }
        });
        $(document).bind('signalPageUpdate', ui.setupForms);
        $(document).bind('signalPageUpdate', ui.setupPagination);
        $(document).bind('signalPageUpdate', ui.setupAutocomplete);
        
        $(document).bind('signalPlaylistTrackModificationRequest', function(e, track, playlist, action, element) {
            /* read playlist_track_modify first */
            var data = {}
            
            if (track.pk != undefined) {
                data['track_pk'] = track.pk;
            }
            else if (track.name != undefined) {
                data['track_name'] = track.name;
            }
            
            if (track.artist != undefined && track.artist.name != undefined) {
                data['artist_name'] = track.artist.name;
            }

            if (playlist.pk != undefined) {
                data['playlist_pk'] = playlist.pk;
            }
            else if (playlist.name != undefined) {
                data['playlist_name'] = playlist.name;
            }

            if (action != undefined) {
                data['action'] = action;
            }
        
            if (!user.is_authenticated) {
                ui.authenticationPopup()
            } else if (element && element.hasClass('direct_to_playlist')) {
                data['direct_to_playlist'] = 1;
                //var song_info = element.parents('li.song_info');
                // faster, less resistent to changes in apps/music/templates/music/_render_tracks.html
                var song_info = element.parent().clone();

                $.ajax({
                    url: playlist_track_modify,
                    dataType: 'html',
                    data: data,
                    type: 'post',
                    success: function(html, textStatus, request) {
                        var ul = $('div.playlist_track_list ul.song_list');
                        var last = ul.find('li.song_info:last');
                        if (last) {
                            if (last.hasClass('dd') && song_info.hasClass('dd')) {
                                song_info.removeClass('dd');
                            } else if (last.hasClass('dd') == false && song_info.hasClass('dd') == false) {
                                song_info.addClass('dd');
                            }
                            var n = parseInt(last.find('span.number').html()) + 1;
                            if (!n) {
                                n = 1;
                            }
                            song_info.find('span.number').html(n);
                        }
                        ul.append(song_info);
                        $('#ajaxload').fadeOut();
                    },
                    beforeSend: ui.beforeSend,
                    error: ui.error,
                });
            } else {
                ui.popup(playlist_track_modify + '?' + $.param(data));
            }
        });

        this.ready = true;
    },
    'setupLinks': function() {
        if (!ui.settings['ajaxEnable']) {
            return undefined;
        }

        $('a:not(a.ui_ignore)').live('click', function(e) {
            e.preventDefault();
            var url = $(this).attr('href');
            if ($(this).hasClass('authenticationRequired') && !user.is_authenticated) {
                ui.authenticationPopup(url);
            } else if ($(this).hasClass('simplemodal-contain')) {
                $.ajax({
                    url: url,
                    dataType: 'html',
                    success: function(html, textStatus, request) {
                        $('#simplemodal-data').html(html);
                        $(document).trigger('signalPageUpdate', [url]);
                        $('#ajaxload').fadeOut();
                    },
                    beforeSend: ui.beforeSend,
                    error: ui.error,
                });               
            } else if ($(this).hasClass('popup')) {
                ui.popup(url);
            } else {
                $.history.load(url);
            }
        });

        $('.delete.parent').live('click', function(e) {
            e.preventDefault();
            $(this).parent().remove();
        });
    },
     'setupForms': function() {
        if (ui.settings['ajaxEnable'] && $('form').length) {
            $('form:not(.ui_ignore)').submit(function(e) {
                e.preventDefault();
                var url = $(this).attr('action');
    
                $.ajax({
                    url: url,
                    dataType: 'html',
                    data: $(this).serialize(),
                    type: $(this).attr('method'),
                    success: function(html, textStatus, request) {
                        $('#page_body_container').html(html);
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
        if (!ui.settings['ajaxEnable']) {
            return false;
        }

        if ($('div.pagination:not(.virtual)').length) {
            $('div.pagination a').each(function() {
                var href = $(this).attr('href');
                if (href.match(/^\?/)) {
                    $(this).attr('href', ui.currentUrl.replace(/\?page=.*$/, '') + href);
                }
            });
        }

        // todo: move to live()
        if ($('div.pagination.virtual').length) {
            $('div.pagination a.page.ui_ignore').click(function() {
                var page = $(this).attr('class').match(/page_([0-9]+)/)[1];
                $('.page_item').hide();
                $('.page_item.page_'+ page).show();
            });
        }
    },
    'setupAutocomplete': function() {
        if ($('input.autocomplete#term').length == 0) {
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
            
            $('input.autocomplete#term').jsonSuggest(function() {
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
        var currentRequest = ui.currentRequest;
        ui.currentRequest = req;
        if (currentRequest && currentRequest != req) {
            currentRequest.abort()
        }
    },
    'error': function(req, textStatus) {
        if (ui.currentRequest == req) { 
            /* failed */
            ui.currentUrl = false;
            $('#ajaxload').fadeOut();
            alert('Sorry but your request failed. Our techies have been notified by mail and will take care of it');
        } else { 
            /* aborted */
        }
    },
    'authenticationPopup': function(url) {
        var next = '';
        if (url) {
            next = '&next=' + encodeURIComponent(url);
        }
        this.popup(popup_auth + '?modal=1' + next);
    },
    'popup': function(url, method, data) {
        if (method == undefined) {
            method = 'get';
        }

        if (!url.match(/modal/)) {
            if (!url.match(/\?/)) {
                url += '?'
            }
            url += '&modal=1';
        }

        $.ajax({
            url: url,
            dataType: 'html',
            type: method,
            success: function(html, textStatus, request) {
                $.modal(html);
                $('#simplemodal-data').before($('#page_title').clone().attr('id', 'simplemodal-title'));
                $(document).trigger('signalPopupOpen');
                $('#ajaxload').fadeOut();
            },
            beforeSend: ui.beforeSend,
            error: ui.error,
        });
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
                        $('#page_body_container').html(html);
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
