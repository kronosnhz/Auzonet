$(document).ready(function(){
    $('#form-new-community').hide();
    $('#id_password').prop( "disabled", true );
    $('#id_access_type').on("change", function(){
        if($('#id_access_type').val() == 'PU') {
            $('#id_password').prop( "disabled", true );
        }
        else if ($('#id_access_type').val() == 'PR') {
            $('#id_password').prop( "disabled", false );
        }
    });
});

$('#btn-new-community').on("click", function(){
    $('#form-join-existing').fadeOut(function(){
        $('#form-new-community').fadeIn();

    });
});
$('#btn-cancel').on("click", function(event){
    event.preventDefault()
    $('#form-new-community').fadeOut(function(){
        $('#form-join-existing').fadeIn();
    });
});
$('#btn-back').on("click", function(event){
    event.preventDefault()
    $('#form-new-community').fadeOut(function(){
        $('#form-join-existing').fadeIn();
    });
});