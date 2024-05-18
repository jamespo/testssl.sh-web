#!/usr/bin/env python3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from flask import Flask, Response, request, render_template, flash, stream_with_context
import os
from os import urandom
from subprocess import Popen, PIPE
import re
import socket

SENTINEL = '------------SPLIT----------HERE---------'

application = Flask(__name__)

### Configuration ###
checkCmd = os.environ.get("TESTSSL_CMD", "testssl.sh/testssl.sh")
checkArgs = ["--quiet", "--add-ca=%s" % os.environ.get("TESTSSL_CA",
                                                       "/etc/ssl/certs/ca-certificates.pem")]
checkTimeout = int(os.environ.get("CHECKTIMEOUT", default=300))
testsslDebug = int(os.environ.get("TESTSSLDEBUG", default=0))
rendererCmd = "aha"
rendererArgs = ["-n"]
rendererTimeout = 30
protocols = ["ftp", "smtp", "pop3", "imap", "xmpp", "telnet", "ldap"]
scantypes = ["normal", "quick"]
reHost = re.compile("^[a-zA-Z0-9_][a-zA-Z0-9_-]+(.[a-zA-Z0-9_-]+)*$")
preflightRequest = True
preflightTimeout = 10
application.debug = False
application.secret_key = urandom(32)
#####################

def sanity_checks(request):
    """run sanity checks on input"""
    ok = True
    host = request.form['host']
    if not reHost.match(host):
        flash("Wrong host name!")
        ok = False
    if host == "localhost" or host.find("127.") == 0 or host == "::1":
        flash("I was already pentested ;)")
        ok = False

    try:
        port = int(request.form['port'])
        if not (port >= 0 and port <= 65535):
            flash("Wrong port number!")
            ok = False
    except:
        flash("Port number must be numeric")
        ok = False

    scantype = request.form['scantype']
    if scantype not in scantypes:
        flash("Wrong scantype!")
        ok = False

    starttls = ('starttls' in request.form and request.form['starttls'] == "yes")

    protocol = request.form['protocol']
    if starttls and protocol not in protocols:
        flash("Wrong protocol!")
        ok = False

    return (ok, starttls, scantype, host, port, protocol)


@application.route("/", methods=['GET', 'POST'])
def main():

    if request.method == 'GET':                         # Main Page
        return render_template("main.html")
    elif request.method == 'POST':                      # Perform Test
        # check request values
        (ok, starttls, scantype, host, port, protocol) = sanity_checks(request)

        # Perform preflight request to prevent that testssl.sh runs into long timeout
        if ok and preflightRequest:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(preflightTimeout)
                s.connect((host, port))
                s.close()
            except:
                flash("Connection failed!")
                ok = False

        if not ok:
            return render_template("main.html")

        # Build command line
        testssl_args = [checkCmd, *checkArgs]

        testssl_args.append("--debug="+str(testsslDebug))

        if scantype == "normal":
            # testssl_args += ["--protocols", "--cipher-per-proto", "--fs", "--rc4", "--vulnerable"]
            pass
        elif scantype == "quick":
            testssl_args += ["--protocols", "--cipher-per-proto", "--server-defaults"]

        if starttls:
            testssl_args.append("-t")
            testssl_args.append(protocol)

        testssl_args.append(host + ":" + str(port))

        # Build render command line
        render_args = [rendererCmd, *rendererArgs]

        # Perform test

        def runtest():
            first, _, last = render_template('result.html', result=SENTINEL).partition(SENTINEL)
            yield first
            check = Popen(testssl_args, shell=False, stdout=PIPE, stderr=PIPE)
            for line in iter(check.stdout.readline, b''):
                renderer = Popen(render_args, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                html, err = renderer.communicate(input=line)
                if renderer.returncode != 0:
                    html = "<pre>HTML formatting failed with error code " + str(renderer.returncode) + " - see raw output below</pre>"
                    html += "<pre>" + str(err, 'utf-8') + "</pre>"
                    yield str(html, 'utf-8')
                    break
                yield str(html, 'utf-8')
            output, err = check.communicate(timeout=checkTimeout)
            if check.returncode > 128:
                yield str(err, 'utf-8')
            yield last
            check.kill()
            renderer.kill()

        return Response(stream_with_context(runtest()), mimetype='text/html')


@application.route("/about/")
def about():
    # Build commmands
    testssl_args = [checkCmd]
    testssl_args.append("--version")
    render_args = [rendererCmd]
    render_args += rendererArgs
    # Get version output from testssl
    check = Popen(testssl_args, shell=False, stdout=PIPE, stderr=PIPE)
    output, _ = check.communicate()
    # Render output as HTML
    renderer = Popen(render_args, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    html, _ = renderer.communicate(input=output)
    check.kill()
    renderer.kill()
    return render_template("about.html", about=str(html, 'utf-8'))

if __name__ == "__main__":
    application.run(host=os.environ.get("TESTSSL_WEB_HOST", "0.0.0.0"),
                    port=int(os.environ.get("TESTSSL_WEB_PORT", 5000)))
