// ajax search queries through input form
$(document).ready(function () {
  $("#keywordForm").submit(function (event) {
      
      event.preventDefault();

      // (1.1) get search results
      $.ajax({
          type: "POST",
          data: {
              search_results: true,
              search_query: $('#id_keyword').val(), // from form
              csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
              action: 'post'
          },
          success: function (returnedData) {
              $( '#search_results_div' ).html( returnedData );

          // (1.2) get search results
          $.ajax({
            type: "POST",
            data: {
                search_query: $('#id_keyword').val(), // from form
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                action: 'post'
            },
            success: function (returnedData) {
                $( '#last_searched_div' ).html( returnedData );
            }
          });
          }
      });

      // (2) get suggested words 
      $.ajax({
        type: "POST",
        data: {
            find_similar: true,
            search_query: $('#id_keyword').val(), // from form
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function (returnedData) {
            $( '#similar_words_div' ).html( returnedData );
        }
      });


    return false; 
  });

});


// ajax search queries - linked from suggestions
function searchKeyword(val){
  event.preventDefault();

    // (1.1) get search results
      $.ajax({
        type: "POST",
        data: {
            search_results: true,
            search_query: val, // from form
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function (returnedData) {
          $( '#search_results_div' ).html( returnedData );
          // (1.2) get search results
          $.ajax({
            type: "POST",
            data: {
                search_query: val, // from form
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                action: 'post'
            },
            success: function (returnedData) {
                $( '#last_searched_div' ).html( returnedData );
            }
          });
      }
    });

    // (2) get suggested words 
    $.ajax({
      type: "POST",
      data: {
          find_similar: true,
          search_query: val, // from form
          csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
          action: 'post'
      },
      success: function (returnedData) {
        $( '#similar_words_div' ).html( returnedData );
      }
    });


}
