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

    $("#id_tags").on("itemAdded", function(event) {
      // TODO
    });

    $("#id_tags").on("itemRemoved", function(event) {
      // TODO
    });

    // set sidebar height
    $('#sidebar').css("height", window.innerHeight - 55 );

    $(document).ready(function(){
       $("#delete-note").click(function(e){
            e.preventDefault();
            if (window.confirm("Are you sure?")) {
               $("#delete-note-form").submit();
           }
       });
    });

}); })(jQuery);

function tagClicked(tag) {
  
}
