# bugzilla3.py - a Python interface to Bugzilla 3.x using xmlrpclib.
#
# Copyright (C) 2008, 2009 Red Hat Inc.
# Author: Will Woods <wwoods@redhat.com>
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import bugzilla.base

class Bugzilla3(bugzilla.base.BugzillaBase):
    '''Concrete implementation of the Bugzilla protocol. This one uses the
    methods provided by standard Bugzilla 3.0.x releases.'''

    version = '0.1'
    user_agent = bugzilla.base.user_agent + ' Bugzilla3/%s' % version

    def __init__(self,**kwargs):
        bugzilla.base.BugzillaBase.__init__(self,**kwargs)
        self.user_agent = self.__class__.user_agent

    def _login(self,user,password):
        '''Backend login method for Bugzilla3'''
        return self._proxy.User.login({'login':user,'password':password})

    def _logout(self):
        '''Backend login method for Bugzilla3'''
        return self._proxy.User.logout()

    #---- Methods and properties with basic bugzilla info 

    def _getuserforid(self,userid):
        '''Get the username for the given userid'''
        # STUB FIXME
        return str(userid)

    # Connect the backend methods to the XMLRPC methods
    def _getbugfields(self):
        '''Get a list of valid fields for bugs.'''
        # XXX BZ3 doesn't currently provide anything like the getbugfields()
        # method, so we fake it by looking at bug #1. Yuck.
        keylist = self._getbug(1).keys()
        if 'assigned_to' not in keylist:
            keylist.append('assigned_to')
        return keylist
    def _getproducts(self):
        '''This throws away a bunch of data that RH's getProdInfo
        didn't return. Ah, abstraction.'''
        product_ids = self._proxy.Product.get_accessible_products()
        r = self._proxy.Product.get_products(product_ids)
        return r['products']
    def _getcomponents(self,product):
        if type(product) == str:
            product = self._product_name_to_id(product)
        r = self._proxy.Bug.legal_values({'product_id':product,'field':'component'})
        return r['values']

    #---- Methods for reading bugs and bug info

    def _getbugs(self,idlist):
        '''Return a list of dicts of full bug info for each given bug id'''
        r = self._proxy.Bug.get_bugs({'ids':idlist, 'permissive': 1})
        return [i['internals'] for i in r['bugs']]
    def _getbug(self,id):
        '''Return a dict of full bug info for the given bug id'''
        return self._getbugs([id])[0]
   # Bugzilla3 doesn't have getbugsimple - alias to the full method(s)
    _getbugsimple = _getbug
    _getbugssimple = _getbugs

    #---- createbug - call to create a new bug

    createbug_required = ('product','component','summary','version',
                          'op_sys','platform')
    def _createbug(self,**data):
        '''Raw xmlrpc call for createBug() Doesn't bother guessing defaults
        or checking argument validity. Use with care.
        Returns bug_id'''
        r = self._proxy.Bug.create(data)
        return r['id']

    #---- Methods for interacting with users

    def _createuser(self, email, name=None, password=None):
        '''Create a new bugzilla user directly.

        :arg email: email address for the new user
        :kwarg name: full name for the user
        :kwarg password: a password to use with the account
        '''
        userid = self._proxy.User.create(email, name, password)
        return userid

# Bugzilla 3.2 adds some new goodies on top of Bugzilla3.
class Bugzilla32(Bugzilla3):
    '''Concrete implementation of the Bugzilla protocol. This one uses the
    methods provided by standard Bugzilla 3.2.x releases.

    For further information on the methods defined here, see the API docs:
    http://www.bugzilla.org/docs/3.2/en/html/api/
    '''

    version = '0.1'
    user_agent = bugzilla.base.user_agent + ' Bugzilla32/%s' % version
    createbug_required = ('product','component','summary','version')

    def _addcomment(self,id,comment,private=False,
                   timestamp='',worktime='',bz_gid=''):
        '''Add a comment to the bug with the given ID. Other optional 
        arguments are as follows:
            private:   if True, mark this comment as private.
            timestamp: Ignored by BZ32.
            worktime:  amount of time spent on this comment, in hours
            bz_gid:    Ignored by BZ32.
        '''
        return self._proxy.Bug.add_comment({'id':id,
                                            'comment':comment,
                                            'private':private,
                                            'work_time':worktime})

# Bugzilla 3.4 adds some new goodies on top of Bugzilla32.
class Bugzilla34(Bugzilla32):
    version = '0.2'
    user_agent = bugzilla.base.user_agent + ' Bugzilla34/%s' % version

    def _getusers(self, ids=None, names=None, match=None):
        '''Return a list of users that match criteria.

        :kwarg ids: list of user ids to return data on
        :kwarg names: list of user names to return data on
        :kwarg match: list of patterns.  Returns users whose real name or
            login name match the pattern.
        :raises xmlrpclib.Fault: Code 51: if a Bad Login Name was sent to the
                names array.
            Code 304: if the user was not authorized to see user they
                requested.
            Code 505: user is logged out and can't use the match or ids
                parameter.

        Available in Bugzilla-3.4+
        '''
        params = {}
        if ids:
            params['ids'] = ids
        if names:
            params['names'] = names
        if match:
            params['match'] = match
        if not params:
            raise bugzilla.base.NeedParamError('_get() needs one of ids,'
                    ' names, or match kwarg.')

        return self._proxy.User.get(params)

    def _search(self,query):
        '''Search bugzilla and return a list of matching bugs.
        query must be a dict with fields like those in in querydata['fields'].
        Returns a dict like this: {'bugs':buglist,
                                   'displaycolumns':columnlist,
                                   'sql':querystring}
        buglist is a list of dicts describing bugs. You can specify which 
        columns/keys will be listed in the bugs by setting 'column_list' in
        the query; otherwise the default columns are used (see the list in
        querydefaults['default_column_list']). The list of columns will be
        in 'displaycolumns', and the SQL query used by this query will be in
        'sql'. 
        ''' 
        return self._proxy.Bug.search(query)

    def _comments(self, id_list):
        return self._proxy.Bug.comments({'ids': id_list})
