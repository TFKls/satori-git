function createFileUploadInstance(form_id, input_name, remove_url) {
    var fid = $('#'+form_id+' input[name='+input_name+']').val();
    var actualFilesList = {};
    $(function() {
        $('#files input[name="rfile"]').each(function() {
            actualFilesList[$(this).val()] = true;
        });
    });

    $(function() {
        var removedFilesCounter = 0;
        $('.remove_existing').submit(function(event) {
            event.preventDefault();
            var form = $(event.target); rfile = form.find('input').val();

            $('#edit_form').append(
                '<input type="hidden" name="rfile_' + removedFilesCounter + 
                '" value="' + rfile + '">'
            );
            delete actualFilesList[rfile];
            removedFilesCounter = removedFilesCounter + 1;
            $(event.target).parent().parent().remove();
            return false;
        });
    });

    $(function () {
        var notCompletedCounter = 0;
        var $wrongFileDialog = $('<div></div>')
                .html('File with a given name already exists!')
                .dialog({
                    autoOpen: false,
                    resizable: false,
                    title: 'Wrong file name'
                });
        $wrongFileDialog.css('font-size: 62.5%');
        $('#file_upload').fileUploadUI({
            uploadTable: $('#files'),
            downloadTable: $('#files'),
            beforeSend: function (event, files, index, xhr, handler, callBack) {
                ex = 0;
                if (actualFilesList[files[index].name]) {
                    handler.removeNode(handler.uploadRow);
                    $wrongFileDialog.dialog("open");
                    return;
                }
                if (files[index].size > 10000000) {
                    handler.uploadRow.find('.file_upload_progress').html(' FILE IS TOO BIG!');
                    setTimeout(function () {
                        handler.removeNode(handler.uploadRow);
                    }, 5000);
                    return;
                }
                actualFilesList[files[index].name] = true;
                $("#create_subpage").attr("disabled", true);
                notCompletedCounter = notCompletedCounter + files.length;
                callBack();
            },
            buildUploadRow: function (files, index) {
                return $('<tr><td>' + files[index].name + '<\/td>' +
                        '<td class="file_upload_progress"><div><\/div><\/td>' +
                        '<td class="file_upload_cancel">' +
                        '<button class="ui-state-default ui-corner-all" title="Cancel">' +
                        '<span class="ui-icon ui-icon-cancel">Cancel<\/span>' +
                        '<\/button><\/td><\/tr>');
            },
            buildDownloadRow: function (file) {
                return $('<tr><td>' + file.name + '<\/td>' + 
                        '<td><form><button class="ui-state-default ui-corner-all" type="submit">'+
                        '<span class="ui-icon ui-icon-trash"><\/span>'+
                        '<\/button><\/form><\/td><\/tr>');
            },
            onAbort: function (event, files, index, xhr, handler) {
                handler.removeNode(handler.uploadRow);
                delete actualFilesList[files[index].name];
            },
            onComplete: function (event, files, index, xhr, handler) {
                notCompletedCounter = notCompletedCounter - files.length;
                if (notCompletedCounter == 0) {
                    $("#create_subpage").attr("disabled", false);
                }
                handler.downloadRow.find('form').submit(function(event) {
                    event.preventDefault();
    /*                $('#loading').fadeIn();*/
                    $.ajax({
                        data: {
                            fid : fid,
                            filename : files[index].name
                        },
                        url: remove_url, 
                        type: 'POST',
                        success: function (data) {
                            /*$('#loading').fadeOut();*/
                            delete actualFilesList[files[index].name];
                            handler.downloadRow.remove();
                        }
                    });
                    return false;
                });
            }
        });
    });
}
