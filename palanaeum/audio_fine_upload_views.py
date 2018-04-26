# Taken from https://github.com/FineUploader/server-examples
# Changes made for compatibility
import json
import logging
import os
import os.path
import pathlib
import random
import shutil
import string

from django import forms
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from palanaeum.models import AudioSource, Event

logger = logging.getLogger('palanaeum.fine_uploader')


class UploadFileForm(forms.Form):
    """
    This form represents a basic request from Fine Uploader.
    The required fields will **always** be sent, the other fields are optional
    based on your setup.
    Edit this if you want to add custom parameters in the body of the POST
    request.
    """
    qqfile = forms.FileField()
    qquuid = forms.CharField()
    qqfilename = forms.CharField()
    qqpartindex = forms.IntegerField(required=False)
    qqchunksize = forms.IntegerField(required=False)
    qqpartbyteoffset = forms.IntegerField(required=False)
    qqtotalfilesize = forms.IntegerField(required=False)
    qqtotalparts = forms.IntegerField(required=False)


def combine_chunks(total_parts, total_size, source_folder, dest):
    """
    Combine a chunked file into a whole file again. Goes through each part,
    in order, and appends that part's bytes to another destination file.
    Chunks are stored in media/chunks
    Uploads are saved in media/uploads
    """

    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))

    with open(dest, 'wb+') as destination:
        for i in range(total_parts):
            part = os.path.join(source_folder, str(i))
            with open(part, 'rb') as source:
                destination.write(source.read())


def save_upload(f, path):
    """
    Save an upload. Django will automatically "chunk" incoming files
    (even when previously chunked by fine-uploader) to prevent large files
    from taking up your server's memory. If Django has chunked the file, then
    write the chunks, otherwise, save as you would normally save a file in
    Python.
    Uploads are stored in media/uploads
    """
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, 'wb+') as destination:
        if hasattr(f, 'multiple_chunks') and f.multiple_chunks():
            for chunk in f.chunks():
                destination.write(chunk)
        else:
            destination.write(f.read())


def make_response(status=200, content_type='text/plain', content=None):
    """
    Construct a response to an upload request.
    Success is indicated by a status of 200 and { "success": true }
    contained in the content.
    Also, content-type is text/plain by default since IE9 and below chokes
    on application/json. For CORS environments and IE9 and below, the
    content-type needs to be text/html.
    """
    response = HttpResponse()
    response.status_code = status
    response['Content-Type'] = content_type
    response.content = content
    return response


class UploadView(View):
    """
    View which will handle all upload requests sent by Fine Uploader.
    See: https://docs.djangoproject.com/en/dev/topics/security/#user-uploaded-content-security
    Handles POST and DELETE requests.
    """

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UploadView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        A POST request. Validate the form and then handle the upload
        based ont the POSTed data. Does not handle extra parameters yet.
        """
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_upload(request.FILES['qqfile'], form.cleaned_data, request)
            return make_response(content=json.dumps({'success': True}))
        else:
            return make_response(
                status=400,
                content=json.dumps({
                    'success': False,
                    'error': '%s' % repr(form.errors)
                }))

    def delete(self, request, *args, **kwargs):
        """
        A DELETE request. If found, deletes a file with the corresponding
        UUID from the server's filesystem.
        """
        qquuid = kwargs.get('qquuid', '')
        if qquuid:
            try:
                handle_deleted_file(qquuid)
                return make_response(content=json.dumps({ 'success': True }))
            except Exception as e:
                return make_response(
                    status=400,
                    content=json.dumps({
                        'success': False,
                        'error': '%s' % repr(e)
                    }))
        return make_response(
            status=404,
            content=json.dumps({
                'success': False,
                'error': 'File not present'
            }))


def handle_upload(f, fileattrs, request):
    """
    Handle a chunked or non-chunked upload.
    """
    logger.info(fileattrs)

    chunked = False
    dest_folder = os.path.join(settings.UPLOAD_DIRECTORY, fileattrs['qquuid'])
    dest = os.path.join(dest_folder, fileattrs['qqfilename'])

    # Chunked
    if fileattrs.get('qqtotalparts') and int(fileattrs['qqtotalparts']) > 1:
        chunked = True
        dest_folder = os.path.join(settings.CHUNKS_DIRECTORY, fileattrs['qquuid'])
        dest = os.path.join(dest_folder, fileattrs['qqfilename'], str(fileattrs['qqpartindex']))
        logger.info('Chunked upload received')

    save_upload(f, dest)
    logger.info('Upload saved: %s' % dest)

    # If the last chunk has been sent, combine the parts.
    if chunked:
        chunks_on_disk = len(os.listdir(os.path.join(dest_folder, fileattrs['qqfilename'])))
        if fileattrs['qqtotalparts'] == chunks_on_disk:
            logger.info('Combining chunks: %s' % os.path.dirname(dest))
            dest_dir = os.path.join(settings.UPLOAD_DIRECTORY, fileattrs['qquuid'], fileattrs['qqfilename'])
            combine_chunks(fileattrs['qqtotalparts'], fileattrs['qqtotalfilesize'],
                           source_folder=os.path.dirname(dest), dest=dest_dir)
            logger.info('Combined: %s' % dest)

            shutil.rmtree(os.path.dirname(os.path.dirname(dest)))
            upload_finished(request)
    else:
        upload_finished(request)

    return


def handle_deleted_file(uuid):
    """ Handles a filesystem delete based on UUID."""
    logger.info(uuid)

    loc = os.path.join(settings.UPLOAD_DIRECTORY, uuid)
    shutil.rmtree(loc)


def randomize_name(file_name: pathlib.Path) -> pathlib.Path:
    """
    Add a random set of characters to the end of file name.
    """
    rand_tag = ''.join(random.sample(string.ascii_letters, 5))
    name = file_name.name
    suffix = "".join(file_name.suffixes)
    name = name.replace(suffix, "_{}{}".format(rand_tag, suffix))
    return file_name.with_name(name)


@csrf_exempt
def upload_finished(request):
    """
    Handle the completed upload.

    Fields in POST:
    qquuid - uuid of the file
    qqfilename - original filename of the file
    qqtotalfilesize - size of the file
    eventId - id of the event the files should be added to
    """
    event = get_object_or_404(Event, pk=request.POST['eventId'])
    file_path = pathlib.Path(settings.UPLOAD_DIRECTORY, request.POST['qquuid'], request.POST['qqfilename'])
    dest_path = pathlib.Path(settings.MEDIA_ROOT, 'sources', request.POST['eventId'], request.POST['qqfilename'])
    dest_path = randomize_name(pathlib.Path(str(dest_path).replace(' ', '_')))

    if not file_path.exists():
        return HttpResponse(status=404)

    dest_path.parent.mkdir(parents=True, exist_ok=True, mode=0o775)
    shutil.move(str(file_path), str(dest_path))

    asrc = AudioSource()
    asrc.event = event
    asrc.length = 0
    asrc.original_filename = dest_path.name
    asrc.raw_file = str(dest_path.relative_to(settings.MEDIA_ROOT))
    asrc.created_by = request.user
    asrc.is_approved = request.user.is_staff
    asrc.file_title = dest_path.name
    asrc.save()
    from palanaeum import tasks
    tasks.transcode_source.delay(asrc.id)

    return HttpResponse(status=200)
