/*
 * Copyright (c) 2009 Tom Coote (http://www.tomcoote.co.uk)
 * This is licensed under GPL (http://www.opensource.org/licenses/gpl-license.php) licenses.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

/*jslint  eqeqeq: true, browser: true */
/*global jQuery */
 
/**
 * Turn a text box into an auto suggest box which search's and 
 * displays results specified in a JSON string
 * 
 *
 * @name jsonSuggest
 * @type jQuery
 * @param searchData :	[required] Can be one of three things; a JSON string which specified the search data, an object that is representative of a parsed JSON string or a function which returns either of these two things.
 *					expected object format example; (either as raw object or JSON string)
 					[
						{
							id: 1,
							text: 'Thomas',
							image: 'img/avator1.jpg',	// optional
							extra: 'www.thomas.com'	// optional
						},
						{
							id: 2,
							text: 'Frederic',
							image: 'img/avator2.jpg',	// optional
							extra: 'www.freddy.com'	// optional
						},
						{
							id: 2,
							text: 'James',
							image: 'img/avator2.jpg',	// optional
							extra: 'www.james.com'	// optional
						}
					]
 * @param Object settings;	[optional]
 *			minCharacters :	[default 1] Number of characters that the input should accept before running a search.
 *			maxResults:	[default undefined] If set then no more results than this number will be found.
 *			wildCard :		[default ''] A character to be used as a match all wildcard when searching. Leaving empty will mean results are matched inside
 *						strings but if a wildCard is present then results are matched from the beginning of strings.
 *			caseSensitive :	[defautl false] True if the filter search's are to be case sensitive.
 *			notCharacter :	[default !] The character to use at the start of any search text to specify that the results should NOT contain the following text.
 *			maxHeight :	[default 350] This is the maximum height that the results box can reach before scroll bars are shown instead of getting taller.	
 *			highlightMatches: [default true] This will add strong tags around the text that matches the search text in each result.
 *			onSelect : 		[default undefined] Function that gets called once a result has been selected, gets passed in the object version of the result as specified in the json string
 *			ajaxResults : 	[default false] If this is set to true then you must specify a function as the searchData construction parameter. This is because when this
 *						settings is true then results are retrieved from an external function each time they are needed instead of being retrieved from the data given on 
 * 						contruction. The searchData function must return a JSON string of resulting objects or the object which represents the JSON string. The function is
 *						passed the following paramenters;
 *						1. The search text typed into the input box
 *						2. The current wildCard setting
 *						3. The current caseSensitive setting
 *						4. The current notCharacter setting 
 *			width:		[default undefined] If set this will become the width of the results box else the box will be the same width as the input
 * @author Tom Coote (www.tomcoote.co.uk)
 * @version 1.2.4
 */

(function($){

	$.fn.jsonSuggest = function(searchData, settings) {
		var defaults = {  
			minCharacters: 1,
			maxResults: undefined,
			wildCard: "",
			caseSensitive: false,
			notCharacter: "!",
			maxHeight: 350,
			highlightMatches: true,
			onSelect: undefined,
			ajaxResults: false,
			width: undefined
			};  
		settings = $.extend(defaults, settings);  
	
		return this.each(function() {
			
			function regexEscape(txt, omit) {
				var specials = ['/', '.', '*', '+', '?', '|',
								'(', ')', '[', ']', '{', '}', '\\'];
				
				if (omit) {
					for (var i=0; i < specials.length; i++) {
						if (specials[i] === omit) { specials.splice(i,1); }
					}
				}
				
				var escapePatt = new RegExp('(\\' + specials.join('|\\') + ')', 'g');
				return txt.replace(escapePatt, '\\$1');
			}
			
			var obj = $(this),
				wildCardPatt = new RegExp(regexEscape(settings.wildCard || ''),'g'),
				results = $('<div />'),
				currentSelection, pageX, pageY;
			
			// When an item has been selected then update the input box,
			// hide the results again and if set, call the onSelect function
			function selectResultItem(item) {
				obj.val(item.text);
				$(results).html('').hide();
				
				if (typeof settings.onSelect === 'function') {
					settings.onSelect(item);
				}
			}

			// Used to get rid of the hover class on all result item elements in the
			// current set of results and add it only to the given element. We also
			// need to set the current selection to the given element here.
			function setHoverClass(el) {
				$('div.resultItem', results).removeClass('hover');
				$(el).addClass('hover');
				
				currentSelection = el;
			}
			
			// Build the results HTML based on an array of objects that matched
			// the search criteria, highlight the matches if feature is turned on in
			// the settings.
			function buildResults(resultObjects, sFilterTxt) {
				sFilterTxt = "(" + sFilterTxt + ")";
			
				var bOddRow = true, i, iFound = 0,
					filterPatt = settings.caseSensitive ? new RegExp(sFilterTxt, "g") : new RegExp(sFilterTxt, "ig");
					
				$(results).html('').hide();
				
				for (i = 0; i < resultObjects.length; i += 1) {
					var item = $('<div />'),
						text = resultObjects[i].text;
						
					if (settings.highlightMatches === true) {
						text = text.replace(filterPatt, "<strong>$1</strong>");
					}
					
					$(item).append('<p class="text">' + text + '</p>');
					
					if (typeof resultObjects[i].extra === 'string') {
						$(item).append('<p class="extra">' + resultObjects[i].extra + '</p>');
					}
					
					if (typeof resultObjects[i].image === 'string') {
						$(item).prepend('<img src="' + resultObjects[i].image + '" />').
							append('<br style="clear:both;" />');
					}
					
					$(item).addClass('resultItem').
						addClass((bOddRow) ? 'odd' : 'even').
						click(function(n) { return function() {
							selectResultItem(resultObjects[n]);						
						};}(i)).
						mouseover(function(el) { return function() { 
							setHoverClass(el); 
						};}(item));
					
					$(results).append(item);
					
					bOddRow = !bOddRow;
					
					iFound += 1;
					if (typeof settings.maxResults === 'number' && iFound >= settings.maxResults) {
						break;
					}
				}
				
				if ($('div', results).length > 0) {
					currentSelection = undefined;
					$(results).show().css('height', 'auto');
					
					if ($(results).height() > settings.maxHeight) {
						$(results).css({'overflow': 'auto', 'height': settings.maxHeight + 'px'});
					}
				}
			}
			
			// Prepare the search string based on the settings for this plugin,
			// run it against each item in the searchData and display any 
			// results on the page allowing selection by the user.
			function runSuggest(e) {	
				if (this.value.length < settings.minCharacters) {
					$(results).html('').hide();
					return false;
				}
				
				var resultObjects = [],
					sFilterTxt = (!settings.wildCard) ? regexEscape(this.value) : regexEscape(this.value, settings.wildCard).replace(wildCardPatt, '.*'),
					bMatch = true, 
					filterPatt, i;
						
				if (settings.notCharacter && sFilterTxt.indexOf(settings.notCharacter) === 0) {
					sFilterTxt = sFilterTxt.substr(settings.notCharacter.length,sFilterTxt.length);
					if (sFilterTxt.length > 0) { bMatch = false; }
				}
				sFilterTxt = sFilterTxt || '.*';
				sFilterTxt = settings.wildCard ? '^' + sFilterTxt : sFilterTxt;
				filterPatt = settings.caseSensitive ? new RegExp(sFilterTxt) : new RegExp(sFilterTxt,"i");
				
				// Get the results from the correct place. If settings.ajaxResults then results are retrieved from
				// an external function each time they are needed else they are retrieved from the data
				// given on contruction.
				if (settings.ajaxResults === true) {
					resultObjects = searchData(this.value, 	settings.wildCard, 
															settings.caseSensitive,
															settings.notCharacter);
															
					if (typeof resultObjects === 'string') {
						resultObjects = JSON.parse(resultObjects);
					}
				}
				else {
					// Look for the required match against each single search data item. When the not
					// character is used we are looking for a false match. 
					for (i = 0; i < searchData.length; i += 1) {
						if (filterPatt.test(searchData[i].text) === bMatch) {
							resultObjects.push(searchData[i]);
						}
					}
				}
				
				buildResults(resultObjects, sFilterTxt);
			}
			
			// To call specific actions based on the keys pressed in the input
			// box. Special keys are up, down and return. All other keys
			// act as normal.
			function keyListener(e) {
				switch (e.keyCode) {
					case 13: // return key
						$(currentSelection).trigger('click');
					
						return false;
					case 40: // down key
						if (typeof currentSelection === 'undefined') {
							currentSelection = $('div.resultItem:first', results).get(0);
						}
						else {
							currentSelection = $(currentSelection).next().get(0);
						}
						
						setHoverClass(currentSelection);
						if (currentSelection) {
							$(results).scrollTop(currentSelection.offsetTop);
						}
						
						return false;
					case 38: // up key
						if (typeof currentSelection === 'undefined') {
							currentSelection = $('div.resultItem:last', results).get(0);
						}
						else {
							currentSelection = $(currentSelection).prev().get(0);
						}
						
						setHoverClass(currentSelection);
						if (currentSelection) {
							$(results).scrollTop(currentSelection.offsetTop);
						}
						
						return false;
					default:
						runSuggest.apply(this, [e]);
				}
			}
			
			// Prepare the input box to show suggest results by adding in the events
			// that will initiate the search and placing the element on the page
			// that will show the results.
			$(results).addClass('jsonSuggestResults').
				css({
					'top': (obj.position().top + obj.height() + 5) + 'px',
					'left': obj.position().left + 'px',
					'width': settings.width || ((obj.width() + 5) + 'px')
				}).hide();
				
			obj.after(results).
				keyup(keyListener).
				blur(function(e) {
					// We need to make sure we don't hide the result set
					// if the input blur event is called because of clicking on
					// a result item.
					var resPos = $(results).offset();
					resPos.bottom = resPos.top + $(results).height();
					resPos.right = resPos.left + $(results).width();
					
					if (pageY < resPos.top || pageY > resPos.bottom || pageX < resPos.left || pageX > resPos.right) {
						$(results).hide();
					}
				}).
				focus(function(e) {
					$(results).css({
						'top': (obj.position().top + obj.height() + 5) + 'px',
						'left': obj.position().left + 'px'
					});
				
					if ($('div', results).length > 0) {
						$(results).show();
					}
				}).
				attr('autocomplete', 'off');
			$().mousemove(function(e) {
				pageX = e.pageX;
				pageY = e.pageY;
			});
			
			// Opera doesn't seem to assign a keyCode for the down
			// key on the keyup event. why?
			if ($.browser.opera) {
				obj.keydown(function(e) {
					if (e.keyCode === 40) { // up key
						return keyListener(e);
					}
				});
			}
			
			// Escape the not character if present so that it doesn't act in the regular expression
			settings.notCharacter = regexEscape(settings.notCharacter || '');
			
			// We need to get the javascript array type data from the searchData setting.
			// Setting can either be a string, already an array or a function that returns one
			// of those things. We only get this data if it isn't being provided using ajax on
			// each search
			if (!settings.ajaxResults) {
				if (typeof searchData === 'function') {
					searchData = searchData();
				}
				if (typeof searchData === 'string') {
					searchData = JSON.parse(searchData);
				}
			}
		});
	};

})(jQuery);