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

        $.ajaxSetup({
            beforeSend: ui.beforeSend,
            error: ui.error,
        });
        $('#ajaxload').ajaxStop(function() {
            $(this).fadeOut();
        });
        $('#ajaxload').ajaxStart(function() {
            $(this).fadeIn();
        });

        $('.comment_form_toggle').live('click', function(e) {
           e.preventDefault();
            $(this).parent().find('.comment_form_contents').toggle('slow');
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
                $('.you_may_also_like li.song_info').slice(0,3).show('slow');
            }

            $('input.magic_value').each(function() {
                var initial = $(this).val();
                $(this).click(function() {
                    if ($(this).val() == initial) {
                        $(this).val('');
                    }
                });
            });
        });
        $(document).bind('signalPopupOpen', ui.setupAutocomplete)
        $(document).bind('signalPopupOpen', ui.twitterCounter)
        $(document).bind('signalPopupOpen', function() {
            var m = ui.currentPopupUrl.match(/tab_id=([^&]+)/)
            if (m == null || m[1] == undefined) {
                $('.simplemodal-data .tab_link:first').trigger('click');
            } else {
                $('.simplemodal-data .tab_link.tab_id_' + m[1]).trigger('click');
            }

            $('#simplemodal-data form.closePopup').submit(function(e) {
                e.preventDefault();
                $.modal.close();

                $.ajax({
                    url: $(this).attr('action'),
                    data: $(this).serialize(),
                    type: $(this).attr('method'),
                    dataType: 'html',
                    success: function(html, textStatus, request) {
                        var htmlnotifications = $(html).find('#user_notifications');
                        if (htmlnotifications.html()) {
                            $('#user_notifications').append(htmlnotifications.html());
                        } else {
                            $('#user_notifications').append('<li>' + html + '</li>');
                        }
                    },
                });
            });
        });

        $(document).bind('signalPopupOpen', ui.setupFacebook);
        $(document).bind('signalPageUpdate', ui.setupFacebook);

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
                    },
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

        // initializes links for ajax requests
        $("a.endless_more").live("click", function() {
            var container = $(this).closest(".endless_container");
            var loading = container.find(".endless_loading");
            $(this).hide();
            loading.show();
            var data = "querystring_key=" + $(this).attr("rel").split(" ")[0];
            $.get($(this).attr("href"), data, function(data) {
                container.before(data);
                container.remove();
            });
            return false;
        });
        $("a.endless_page_link").live("click", function() {
            var data = "querystring_key=" + $(this).attr("rel").split(" ")[0];
            $(this).closest(".endless_page_template").load($(this).attr("href"), data);
            return false;
        }); 

        function hiddenHeight(element)
        {
            var height = 0;
            $(element).children().each(function() {
                height = height + $(this).outerHeight(false);
            });
            return height;
        }

        function scrollBind() {
            $('#page_body_container').scroll(function(){
                var pixelsFromWindowBottomToBottom = 0 + hiddenHeight($(this)) - $(this).scrollTop() - $(this).height();
                if (pixelsFromWindowBottomToBottom < 20) {
                    // temporarily unhook the scroll event watcher so we don't call a bunch of times in a row
                    if ($('a.endless_more').length == 1) {
                        $('#page_body_container').unbind('scroll');
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

        $('a.unlike').live('click', function(e) {
            e.preventDefault();
            var container = $(this).parent().find('div.likes');
            $.get($(this).attr('href'), {}, function() {
                if (container.find('a').length == 1) {
                    container.remove();
                } else {
                    container.find('a.me').remove();
                }
            });
            $(this).fadeOut();
            $(this).next().fadeIn();
        });


        $('a.like').live('click', function(e) {
            e.preventDefault();
            var after = $(this).parent().find('.before_likes');
            var container = $(this).parent().find('div.likes');
            $(this).fadeOut();
            $(this).prev().fadeIn();
            $.get($(this).attr('href'), {}, function() {
                if (!container.length) {
                    var html = []
                    html.push('<div class="topcomments"></div>');
                    html.push('<div class="likes">');
                    html.push('<img src="'+STATIC_URL+'images/not_newthumbup.png" class="espace" />');
                    html.push('<a href="/me" class="me">You like it</a>');
                    html.push('</div>');
                    after.after(html.join(''));
                } else {
                    container.append('<a href="/me" class="me">You like it</a>');
                }
            });
        });

        $(".follow_button, .unfollow_button").live('click', function () {
            $.post($(this).attr("href"), {});
            $(this).parent().find(".follow_button, .unfollow_button").toggle();
            return false
        });

        $('.tab_link').live('click', function(e) {
            var tabid = $(this).attr('class').match(/tab_id_([a-z]*)/)[1];
            $('.tab_content').hide().removeClass('selected');
            $('.tab_content.tab_id_'+tabid).show().addClass('selected');
        });
                
        $('.simplemodal-close').live('click', function() {$.modal.close();});

        $('.add_current_track').click(function(e) {
            var track = player.state.currentTrack;
            var playlist = false;
            $(document).trigger('signalPlaylistTrackModificationRequest', [track, playlist, 'add', $(this)]);
        });
        $('#right_action .share').click(function(e) {
            $('#track_menu').toggle('slow');
        })
        $('.like_current_track').click(function(e) {
            var track = player.state.currentTrack;
            var playlist = { 'pk': tiny_playlist_pk };
            if ($(this).css('backgroundPosition') == '0% 100%') {
                var action = 'remove';
            } else {
                var action = 'add';
            }
            $(document).trigger('signalPlaylistTrackModificationRequest', [track, playlist, action, $(this)]);
            player.tiny_playlist.tracks.push(track);
            if ($(this).css('backgroundPosition') == '0% 100%') {
                $(this).css('backgroundPosition', 'left top');
                $('.song_info.selected .love.icon').css('backgroundPosition', 'left top');
                $('.song_info.selected .love.icon').removeClass('remove_track');
                $('.song_info.selected .love.icon').addClass('add_track');
            } else {
                $(this).css('backgroundPosition', 'left bottom');
                $('.song_info.selected .love.icon').css('backgroundPosition', 'left bottom');
                $('.song_info.selected .love.icon').addClass('remove_track');
                $('.song_info.selected .love.icon').removeClass('add_track');
            }
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
                    },
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
                },
            });
        });
    },
    'notifyUser': function(message) {
        $('#user_notifications').append($('<li class="delete">'+message+' (click to close)</li>'));
    },
    'twitterCounter': function() {
        if ($('.twitter_counter').length < 1) {
            return true;
        }

        textField = $('.twitter_counter')
        textField.keyup(function(e) {
            left = 140 - $(this).val().length;
            $('.twitter_counter_display').html(left);
        });
        textField.trigger('keyup');
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
                var form = $(this);
    
                $.ajax({
                    url: url,
                    dataType: 'html',
                    data: $(this).serialize(),
                    type: $(this).attr('method'),
                    success: function(html, textStatus, request) {
                        if (url == comment_form_target) {
                            var html = []
                            html.push('<div class="comment">');
                            html.push('<a href="/me">');
                            html.push(form.find('img.avatar').parent().html());
                            html.push('</a>');
                            html.push('<a href="/me">You</a> - right now');
                            html.push('<p>');
                            html.push(form.find('textarea').val());
                            html.push('</p>');
                            html.push('</div>');
                            html = html.join('');
                            form.find('textarea').val('');
                            form.parent().parent().prev().append(html);
                        } else {
                            ui.currentUrl = url;
                            $('#page_body_container').html(html);
                            $(document).trigger('signalPageUpdate', [url]);
                        }
                    },
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
        var currentRequest = ui.currentRequest;
        ui.currentRequest = req;
        if (currentRequest && currentRequest != req) {
            currentRequest.abort()
        }
    },
    'error': function(req, textStatus, error) {
        if (textStatus == 'error') {
            if (ui.currentRequest == req) {
                ui.currentUrl = false;
            }
            ui.notifyUser('Sorry but your request failed. Our techies have been notified by mail and will take care of it');
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
        ui.currentPopupUrl = url;

        $.ajax({
            url: url,
            dataType: 'html',
            type: method,
            success: function(html, textStatus, request) {
                $.modal(html);
                $('#simplemodal-data').before($(html).find('#page_title').clone().attr('id', 'simplemodal-title'));
                $(document).trigger('signalPopupOpen');
            },
        });
    },
    'setupFacebook': function() {
        if ($('#fb-root').length < 1) return true;

        function initFb() {
            FB.init({ apiKey: '738ca1d67fa0e795c8a5604278278e8e', status: true, cookie: true, xfbml: true});
        }

        if (ui.facebookJsLoaded == undefined) {
            $.getScript('http://connect.facebook.net/en_US/all.js', initFb);
            ui.facebookJsLoaded = true;
        } else {
            initFb();
        }
    },
}

$(document).ready(function() {
    var urls = [
        //{
            //'urlmatch': /^\/action/,
            //'success': function(html, textStatus, request) {
                //$.history.load(ui.currentUrl);
            //},
        //},
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
                    },
                });
    
                if (!ui.ready) {
                    ui.init();
                }
            }, { unescape: ",/?=" });
        });
    }
});
