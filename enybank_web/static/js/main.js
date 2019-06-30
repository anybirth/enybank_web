// components
function unescapeHTML(str) {
  var div = document.createElement("div");
  div.innerHTML = str.replace(/</g,"&lt;")
                     .replace(/>/g,"&gt;")
                     .replace(/ /g, "&nbsp;")
                     .replace(/\r/g, "&#13;")
                     .replace(/\n/g, "&#10;");
  return div.textContent || div.innerText;
}

function parseDate(input) {
  var parts = String(input).match(/(\d+)/g);
  return new Date(parts[0], parts[1]-1, parts[2]);
}

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
