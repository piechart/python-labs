(function($) { $(function() {
    // allow whole list item to note to be clickable
    $("#notes li").click(function(){
        location.assign($(this).attr("data-url"));
    });

    // add placeholders
    $("#id_title").attr("placeholder", "Title your note");

    // set tags input
    $("#id_tags").attr("placeholder", "Add tag..");
    $("#id_tags").tagsinput();

    // set sidebar height
    $('#sidebar').css("height", window.innerHeight - 55 );

    $(document).ready(function(){
       $("#delete-note").click(function(e){
            e.preventDefault();
            if (window.confirm("Are you sure?")) {
               $("#delete-note-form").submit();
            }
       });

       $("#btn_UpdateNote").click(function(e){
         e.preventDefault();
         for (var instance in CKEDITOR.instances)
            CKEDITOR.instances[instance].updateElement();
         $.ajax({
            url: window.location,
            type: "POST",
            data: {
              csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
              title: $('#id_title').val(),
              tags: $('#id_tags').val(),
              body: $('#id_body').val(),
              next: document.getElementsByName('next')[0].value
            },
            dataType: "plain/text",
            complete: function(xhr, textStatus) {
              if (xhr.status == 200){
                $("#message_block").attr("class", "alert alert-success");
                $("#message_block").html("<strong>Сохранено!</strong> Заметка успешно обновлена.");
              } else {
                $("#message_block").attr("class", "alert alert-danger");
                $("#message_block").html("<strong>Ошибка</strong> Не удалось сохранить заметку.");
              }
              $("#message_block").fadeIn();
              setTimeout(function () {
                $("#message_block").fadeOut();
              }, 1500);
            }
        });
        // ---
       });

    });

}); })(jQuery);

function tagClicked(tag) {
  if (window.confirm("Wanna perform search by tag '" + tag + "'?")) {
     window.location = "/notes/?q=tag:" + tag
  }
}

function onAjaxSuccess(data){
  console.log(data)
}
