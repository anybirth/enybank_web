$(function() {

  // slider
  $('#top-slide').slick({
    autoplay: true,
    autoplaySpeed: 4000,
    speed: 800,
    arrows: false,
    dots: true,
  });

  // datepicker
  $(".date_picker").datepicker({
    showOn: "both",
    buttonImage: "static/main/img/calendar.png",
    buttonImageOnly: true,
    buttonText: "日付を選択",
    dateFormat: "yy-mm-dd",
    beforeShow: function(input, inst) {
      var calendar = inst.dpDiv;
      setTimeout(function() {
        calendar.position({
          my: 'right top',
          at: 'right bottom',
          of: input
        });
      }, 1);
    }
  });

  // easy search
  var start_date = $('[name=start_date]').val();
  var return_date = $('[name=return_date]').val();
  var color_category = ''
  var type = ''

  $('.color_category').on('click', function() {
    color_category = $(this).attr("id");
    var target = '#' + color_category;
    $('.color_category').removeClass('selected');
    $(target).addClass('selected');
    return false;
  });
   $('.type').on('click', function() {
    type = $(this).attr("id");
    var target = '#' + type;
    $('.type').removeClass('selected');
    $(target).addClass('selected');
    return false;
  });

  $('#search').on('click', function() {
    start_date = $('[name=start_date]').val();
    return_date = $('[name=return_date]').val();

    if (start_date && return_date && color_category && type) {
      var _href = $(this).attr("href");
      $(this).attr("href", _href + '?start_date=' + start_date + '&return_date=' + return_date + '&color_category=' + color_category + '&type=' + type);
    } else {
      alert('全ての項目を選択してください');
      return false;
    }
  });
});
