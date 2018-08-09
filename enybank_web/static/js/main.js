$(function() {

  // drawer menu
  var height;
  var scrollpos;
  var header = $('#header').height();

  $('#dummy').css('height', 99999);
  $('#drawer').css('padding-top', header);
  $('#content').css('padding-top', header);

  $('#hamburger').on('click', function() {
    $(this).toggleClass('active');
    if ($(this).hasClass('active')) {
      scrollpos = $(window).scrollTop();
      height = scrollpos - header;
      $('#dummy').fadeIn();
      $('#drawer').animate({height: 'toggle'});
      $('#content').addClass('fixed').css('top', -scrollpos);
    } else {
      $('#dummy').fadeOut();
      $('#drawer').animate({height: 'toggle'}, function() {
        $('#content').removeClass('fixed').css('top', height);
        $('body,html').animate({scrollTop: scrollpos}, 0);
      });
    }
    return false;
  });
});
