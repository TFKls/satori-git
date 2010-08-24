# vim:ts=4:sts=4:sw=4:expandtab

def athina_import():
    import os,sys,getpass
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options] DIR")
    parser.add_option("-U", "--user",
        default='',
        action="store",
        type="string",
        help="Username")
    parser.add_option("-P", "--password",
        default='',
        action="store",
        type="string",
        help="Password")
    (options, args) = parser.parse_args()
    if len(args) != 1:
	    parser.error("incorrect number of arguments")
    if not options.user:
    	options.user = getpass.getuser()
    print 'User: ', options.user
    if not options.password:
    	options.password = getpass.getpass()


    base_dir = args[0]
    if not os.path.exists(os.path.join(base_dir, 'server/contest/users')):
    	raise Exception("Provided path is invalid")
    

    from satori.client.common import Security
    set_token(Security.login(options.user, options.password))

