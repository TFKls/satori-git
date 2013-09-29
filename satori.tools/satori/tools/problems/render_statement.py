# vim:ts=4:sts=4:sw=4:et
import os.path

from satori.client.common import want_import
want_import(globals(), '*')

from satori.tools.problems.common import copy_file, upload_blob

def render_statement(opts):
    with open(opts.STATEMENT) as f:
        statement = f.read()
    attachments = {}
    for attachment in opts.ATTACHMENTS:
        attachments[os.path.basename(attachment)] = upload_blob(attachment)
    out_hash = ProblemStatementUtils.render_to_pdf(statement, attachments)
    out_remote = Blob.open(out_hash)
    with open(opts.OUTPUT, "w") as out_local:
        copy_file(out_remote, out_local)
