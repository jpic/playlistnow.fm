function Artist(kwargs) {
    kwargs = kwargs === undefined ? {} : kwargs;

    this.name = kwargs.hasOwnProperty('name') ? kwargs.name : '';
    this.url = kwargs.hasOwnProperty('url') ? kwargs.url : '';
    this.thumbnail = kwargs.hasOwnProperty('thumbnail') ? kwargs.thumbnail : '';
}
