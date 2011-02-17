var ui = {
    'ready': false,
    'currentRequest': false,
    'currentUrl': document.location.hash.replace(/^#/, ''),
    'settings': {
        'ajaxEnable': true,
    },
    'css': [
        STATIC_URL + "local/reset.css",
        STATIC_URL + "local/screen.css",
        STATIC_URL + "local/prod.css",
        STATIC_URL + "local/tipTip.css",
    ],
    'init': function() {
        $.getScript(STATIC_URL + "jquery.simplemodal.min.js", function() {
        });

        // one time slots
        ui.setupLinks();
        // slots to execute at each update
        $(document).bind('signalPageUpdate', function() {
            if (document.getElementById('page_title')) {
                document.title = $('#page_title').html();
            }
            if ($('.autocomplete_container').length) {
                $('.autocomplete_container').remove();
            }

            $('.tab_link:first').trigger('click');
            $('.tiptip').tipTip();

            if ($('div.you_may_also_like li').length > 0) {
                $('.you_may_also_like li').slice(0,4).show('slow');
            }
        });
        $(document).bind('signalPopupOpen', ui.setupAutocomplete)
        $(document).bind('signalPopupOpen', function() {
            $('.tab_link:first').trigger('click');
            $('#simplemodal-data form.closePopup').submit(function(e) {
                e.preventDefault();
                $.modal.close();

                $.ajax({
                    url: $(this).attr('action'),
                    data: $(this).serialize(),
                    type: $(this).attr('method'),
                    dataType: 'html',
                    success: function(html, textStatus, request) {
                        $('#user_notifications').append($(html).find('#user_notifications').html());
                    },
                    beforeSend: ui.beforeSend,
                    error: ui.error,
                });
            });
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
            } else if (element && element.hasClass('noconfirm')) {
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
                        if (element.hasClass('copy_track_row')) {
                            var ul = $('div.playlist_track_list ul.song_list');
                            if (ul != undefined) {
                                var last = ul.find('li.song_info:last');
                                if (last != undefined) {
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
                                    ul.append(song_info);
                                }
                            }
                        }
                        $('#user_notifications').append($(html).find('#user_notifications').html());
                        $(document).trigger('signalPlaylistUpdate', [data.playlist_pk]);
                        $('#ajaxload').fadeOut();
                    },
                    beforeSend: ui.beforeSend,
                    error: ui.error,
                });
            } else {
                ui.popup(playlist_track_modify + '?' + $.param(data));
            }
        });

        window.setInterval(function() {
            if ($('#user_notifications li').length > 0) {
                var lis = $('#user_notifications li');
                window.setTimeout(function() {
                    lis.fadeOut();
                }, 3000);
            }
        }, 1000);

        function scrollBind() {
            $('#page_body_container').scroll(function(){
                if ($(window).scrollTop() > $(document).height() - ($(window).height()*3)) {
                    // temporarily unhook the scroll event watcher so we don't call a bunch of times in a row
                    if ($('a.endless_more').length == 1) {
                        $(window).unbind('scroll');
                        $("a.endless_more").click();
                        scrollBind();
                    }
                }
            })
        }
        scrollBind();

        $(document).trigger('signalPageUpdate');
        this.ready = true;
    },
    'setupLinks': function() {
        if (!ui.settings['ajaxEnable']) {
            return undefined;
        }

        $('.toggle.tools').live('click', function(e) {
            var li = $(this).parent();
            var ul = $(this).next();
            if (ul.css('display') != 'none') {
                ul.hide('fast');
            } else {
                $('ul.song_tools').hide('slow');
                ul.show('fast');
            }
        });

        $('.tab_link').live('click', function(e) {
            var tabid = $(this).attr('class').match(/tab_id_([a-z]*)/)[1];
            $('.tab_content').hide().removeClass('selected');
            $('.tab_content.tab_id_'+tabid).show().addClass('selected');
        });

        $('a:not(a.endless_more):not(a.ui_ignore):not(a.tab_link)').live('click', function(e) {
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

        $('.delete').live('click', function(e) {
            e.preventDefault();
            if ($(this).hasClass('parent')) {
                var target = $(this).parent();
            } else {
                var target = $(this);
            }

            if ($(this).hasClass('show_next')) {
                var show_next = target.nextAll(':hidden:first');
            } else {
                var show_next = false;
            }

            target.hide('slow', function() {$(this).remove();});

            if (show_next) {
                show_next.show('slow');
            }
        });

        $('.lineFeedContentWhat .delete').live('click', function(e) {
            var pk = $(this).attr('class').match(/action_pk_([0-9]+)/)[1];
            var url = action_delete.replace(/0/, pk);
            var what = $(this);

            $.ajax({
                url: url,
                dataType: 'text',
                data: {},
                type: 'post',
                success: function(html, textStatus, request) {
                    if (what.parents('.lineFeed').find('.lineFeedContent').length > 1) {
                        what.hide('slow');
                    } else {
                        what.parents('.lineFeed').hide('slow');
                    }
                    ui.notifyUser('Thanks for deleting this action');
                    $('#ajaxload').fadeOut();
                },
                beforeSend: ui.beforeSend,
                error: ui.error,
            });
        });
    },
    'notifyUser': function(message) {
        $('#user_notifications').append($('<li class="delete">'+message+' (click to close)</li>'));
    },
    'setupForms': function() {
        if (ui.settings['ajaxEnable'] && $('form').length) {
            $('form:not(.ui_ignore)').submit(function(e) {
                e.preventDefault();


                if ($(this).hasClass('authenticationRequired') && !user.is_authenticated) {
                    ui.authenticationPopup();
                    return false;
                }

                var url = $(this).attr('action');
                if (url == '') {
                    url = ui.currentUrl;
                }
    
                $.ajax({
                    url: url,
                    dataType: 'html',
                    data: $(this).serialize(),
                    type: $(this).attr('method'),
                    success: function(html, textStatus, request) {
                        ui.currentUrl = url;
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
                if (href.match(/^[?&]page/)) {
                    $(this).attr('href', ui.currentUrl.replace(/[?].*$/, '') + href);
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
        $('input.autocomplete').each(function() {
            if ($(this).hasClass('music')) {
                var url = music_search_autocomplete;
            } else if ($(this).hasClass('user')) {
                var url = user_search_autocomplete;
            } else if ($(this).hasClass('playlist')) {
                var url = playlist_search_autocomplete;
            } else if ($(this).hasClass('friends')) {
                var url = friends_search_autocomplete;
            }
    
            var next = $(this).next();
            if (next.hasClass('autocomplete_pk')) {
                var callback = function(value, data) {
                    next.val(data.pk);
                }
            } else {
                var callback = function(value, data) {
                    $.history.load(data['url']); 
                }
            }

            $(this).autocomplete({
                'serviceUrl': url,
                'onSelect': callback,
                'fnFormatResult': function(value, data, currentValue) {
                    return data['html'];
                },
                'deferRequestBy': 0,
            });
        });
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
            ui.notifyUser('Sorry but your request failed. Our techies have been notified by mail and will take care of it');
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
                $('#simplemodal-data').before($(html).find('#page_title').clone().attr('id', 'simplemodal-title'));
                $(document).trigger('signalPopupOpen');
                $('#ajaxload').fadeOut();
            },
            beforeSend: ui.beforeSend,
            error: ui.error,
        });
    }
}


$(document).ready(function() {
    var urls = [
        {
            'urlmatch': /^\/action/,
            'success': function(html, textStatus, request) {
                $.history.load(ui.currentUrl);
            },
        },
    ];

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
                        for(var i in urls) {
                            if(hash.match(urls[i]['urlmatch'])) {
                                var cb=urls[i]['success'];
                                cb(html, textStatus, request);
                                return true;
                            }
                        }

                        $('#page_body_container').html(html);
                        ui.currentUrl = hash;
                        $(document).trigger('signalPageUpdate', [hash]);
                        $('#ajaxload').fadeOut();
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
