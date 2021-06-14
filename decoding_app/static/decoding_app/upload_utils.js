function toggle_num_spk_form(){
    var isDiarChecked = document.getElementById("id_automatic_diarization").checked;
    var numspeakers_divs = document.getElementsByClassName('num_speakers_form');

    for (i = 0; i < numspeakers_divs.length; i++) {
        numspeakers_div = numspeakers_divs[i];
        if(isDiarChecked){
            numspeakers_div.innerHTML = '<small><label class="small" for="numspeakers">num speakers</label><select class="numspeakers_select small" name="numspeakers"><option value="-1">auto</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option><option value="6">6</option>';
        } else {
            numspeakers_div.innerHTML = '';
        } 
    }
}

// dropzone management
var total_duration_transcription = 0;
var override_redirect = 0;

Dropzone.autoDiscover = false;


// -----------------------------
// transcription
// -----------------------------
var dropzone_transcription = new Dropzone("#dropzone_transcript_audio", { 
    autoProcessQueue: false,
    addRemoveLinks: true,
    autoDiscover: false,
    uploadMultiple: true,
    maxFilesize: 200000, // MB (20 Gb)
    maxFiles: 100, 
    parallelUploads: 1, // send requests individually to backend api (max 10)
    timeout: 3000000,
    acceptedFiles:'audio/*,video/*',
    previewTemplate:'<div class="dz-preview dz-file-preview"><div class="dz-image"><img data-dz-thumbnail /></div><div class="dz-details"><div class="dz-size"><span data-dz-size></span></div><div class="dz-filename"><span data-dz-name></span></div></div><div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div><div class="dz-error-message"><span data-dz-errormessage></span></div><div class="num_speakers_form"></div></div>'
    });

$('#uploadfiles_transcription').click(function(){
    event.preventDefault();          

    if (dropzone_transcription.files.length) {

        dropzone_transcription.options.autoProcessQueue = true;
        dropzone_transcription.processQueue(); 

        override_redirect = 1;

    } else {
        alert("Please adds files to upload");                
    } 
});


dropzone_transcription.on("queuecomplete", function() {
    // override_redirect only once queue is processed by clicking upload button 
    // (to avoid redirect if first file rejected and queue complete is called)
    
    console.log("queuecomplete");

    if (override_redirect == 1){
        window.location.replace("/");
    }
});

dropzone_transcription.on("addedfile", function(event) {

    if(document.getElementById("id_automatic_diarization").checked){
        toggle_num_spk_form();
    }   
});
    
dropzone_transcription.on("sending", function(file, xhr, formData) {

    // Get and pass numspeakers field data
    if(document.getElementById("id_automatic_diarization").checked){
        var str = file.previewElement.querySelector(".numspeakers_select").value;
        formData.append("numspeakers_select", str);
    }
});

document.getElementById("id_automatic_diarization").addEventListener('click', function(e){
    toggle_num_spk_form();
});
