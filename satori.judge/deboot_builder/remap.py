from six import print_
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

import os
import sys

class Settings:
    class Passwd:
        def __init__(self, line):
            data = line.split(':')
            self.name = data[0]
            self.uid = int(data[2])
            self.gid = int(data[3])
            self.line = line
        def change_uid(self, dest):
            self.uid = dest
            data = self.line.split(':')
            data[2] = str(self.uid)
            self.line = ':'.join(data)
        def change_gid(self, dest):
            self.gid = dest
            data = self.line.split(':')
            data[3] = str(self.gid)
            self.line = ':'.join(data)
        def __repr__(self):
            return self.line

    class Group:
        def __init__(self, line):
            data = line.split(':')
            self.name = data[0]
            self.gid = int(data[2])
            self.line = line
        def change_gid(self, dest):
            self.gid = dest
            data = self.line.split(':')
            data[2] = str(self.gid)
            self.line = ':'.join(data)
        def __repr__(self):
            return self.line

    def __init__(self, basedir):
        self.basedir = basedir
        self.passwd = {}
        self.group = {}
        with open(os.path.join(basedir, 'etc/passwd')) as passwd:
            for line in passwd.readlines():
            	p = Settings.Passwd(line)
            	self.passwd[p.uid] = p
        with open(os.path.join(basedir, 'etc/group')) as group:
            for line in group.readlines():
            	g = Settings.Group(line)
            	self.group[g.gid] = g
    def commit(self):
        with open(os.path.join(self.basedir, 'etc/passwd'),'w') as passwd:
            for data in sorted(self.passwd.values(),key=lambda p:p.uid):
            	passwd.write(str(data))
        with open(os.path.join(self.basedir, 'etc/group'),'w') as group:
            for data in sorted(self.group.values(),key=lambda g:g.gid):
            	group.write(str(data))
    def remap_uid(self, src, dest):
        passwd = self.passwd[src]
        del self.passwd[src]
        passwd.change_uid(dest)
        self.passwd[passwd.uid] = passwd
        for root, dirs, files in os.walk(self.basedir):
            for item in dirs + files:
                stat = os.lstat(os.path.join(root, item))
                if stat.st_uid == src:
                    os.lchown(os.path.join(root, item), dest, stat.st_gid)
                    if not os.path.islink(os.path.join(root, item)):
                    	os.chmod(os.path.join(root, item), stat.st_mode)
    def remap_gid(self, src, dest):
        group = self.group[src]
        del self.group[src]
        group.change_gid(dest)
        self.group[group.gid] = group
        for passwd in self.passwd.values():
            if passwd.gid == src:
            	passwd.change_gid(dest)
        for root, dirs, files in os.walk(self.basedir):
            for item in dirs + files:
                stat = os.lstat(os.path.join(root, item))
                if stat.st_gid == src:
                    os.lchown(os.path.join(root, item), stat.st_uid, dest)
                    if not os.path.islink(os.path.join(root, item)):
                    	os.chmod(os.path.join(root, item), stat.st_mode)

    def __repr__(self):
        return  'passwd: ' + str(self.passwd) + 'group: ' + str(self.group)

correct = Settings('override_uid_gid')
current = Settings(sys.argv[1])
group_map = {}
passwd_map = {}
group_names = dict([ (g.name, g.gid) for g in correct.group.values() ])
passwd_names = dict([ (p.name, p.uid) for p in correct.passwd.values() ])

group_new = dict()
passwd_new = dict()
ok = True
for g in current.group.values():
    if g.name in group_names:
	    group_map[g.gid] = group_names[g.name]
	else:
		print_('Group ', g.name, ' is incorrect')
		ok = False
for p in current.passwd.values():
    if p.name in passwd_names:
    	passwd_map[p.uid] = passwd_names[p.name]
    else:
		print_('User ', p.name, ' is incorrect')
		ok = False
if not ok:
	sys.exit(1)
free_group = 2000
free_passwd = 2000
while free_group in current.group:
	free_group += 1
while free_passwd in current.passwd:
	free_passwd += 1


def moves(i_map, i_free):
    i_moved = {}
    i_moves = []
    i_finished = {}
    for i in i_map.keys():
        if i in i_finished:
            continue
        if i_map[i] == i:
            continue
        cycle = [ ]
        pos = i
        while True:
            cycle.append(pos)
    	    i_moved[pos] = True
    	    npos = i_map[pos]
            if npos not in i_map or npos in i_finished:
                cycle.reverse()
                for id in cycle:
                    i_moves.append((id, i_map[id]))
                    i_finished[id] = True
                break
            if npos in i_moved:
                cycle.pop()
                i_moves.append((pos, i_free))
                cycle.reverse()
                for id in cycle:
            	    i_moves.append((id, i_map[id]))
                    i_finished[id] = True
                i_moves.append((i_free, i_map[pos]))
                i_finished[pos] = True
                break
            pos = npos
    return i_moves

group_moves = moves(group_map, free_group)
passwd_moves = moves(passwd_map, free_passwd)
print_('GID moves: ', group_moves)
print_('UID moves: ', passwd_moves)


for src,dst in group_moves:
	current.remap_gid(src,dst)
for src,dst in passwd_moves:
	current.remap_uid(src,dst)
current.commit()
