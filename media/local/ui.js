function AjaxUI(configuration) {
    this.configuration = $.merge(configuration, {
        disable: false,
        actions: []
    });
    this.state = {
        lastAction: {
            url: false,
            date: false,
        }
    };
}

function defaultAction(url) {
    this.applies = function() {
        console.log('called applies');
        return true;
    }
}

$(document).ready(function() {
    
});
