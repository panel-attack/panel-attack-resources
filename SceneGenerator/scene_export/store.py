"""Writes the PNG and JSON files the commands hand it, under a root folder by the README's rules: nothing is replaced without a copy in .backup/.
write() and install() leave alone a file edited since the generator wrote it (its sha256 no longer matches
.manifest.json), or one the generator never wrote, unless forced; replace() writes over whatever is there
once it is backed up. The manifest and .backup/ are in the state folder, the root itself unless another is
given."""

import hashlib
import json
import os
import shutil
import time

MANIFEST = '.manifest.json'
BACKUP = '.backup'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    with open(path, 'rb') as f:
        return sha256(f.read())


class Store:
    def __init__(self, root, force=(), clock=None, state=None):
        self.root = os.path.abspath(root)
        self.state = os.path.abspath(state or root)
        self.clock = clock or (lambda: time.strftime('%Y%m%d-%H%M%S'))
        self.force = {self.rel(p) if os.path.isabs(p) else os.path.normpath(p) for p in force}
        self.skipped = []
        self.conflicts = []
        path = os.path.join(self.state, MANIFEST)
        self.manifest = {}
        if os.path.exists(path):
            with open(path) as f:
                self.manifest = json.load(f)

    def rel(self, path):
        rel = os.path.relpath(os.path.abspath(path), self.root)
        if rel == os.pardir or rel.startswith(os.pardir + os.sep):
            raise ValueError('%s is outside %s' % (path, self.root))
        return rel.replace(os.sep, '/')

    def _may_replace(self, rel, path):
        """Whether the existing file at path is the generator's own unedited output, or forced."""
        if rel in self.force:
            return True
        return self.manifest.get(rel) == file_sha256(path)

    def protected(self, path):
        """Whether writing path would be skipped: it exists, was edited or never generated, and isn't forced."""
        return os.path.exists(path) and not self._may_replace(self.rel(path), path)

    def _backup(self, rel, path):
        folder, name = os.path.split(rel)
        stem, ext = os.path.splitext(name)
        target_dir = os.path.join(self.state, BACKUP, folder)
        os.makedirs(target_dir, exist_ok=True)
        stamp = self.clock()
        target = os.path.join(target_dir, '%s-%s%s' % (stem, stamp, ext))
        n = 2
        while os.path.exists(target):
            target = os.path.join(target_dir, '%s-%s-%d%s' % (stem, stamp, n, ext))
            n += 1
        shutil.move(path, target)
        return target

    def _save_manifest(self):
        path = os.path.join(self.state, MANIFEST)
        os.makedirs(self.state, exist_ok=True)
        with open(path + '.tmp', 'w') as f:
            json.dump(dict(sorted(self.manifest.items())), f, indent=1)
            f.write('\n')
        os.replace(path + '.tmp', path)

    def _place(self, path, new_sha, put):
        """Puts new content at path through put(path) when the rules allow; returns what happened."""
        rel = self.rel(path)
        if os.path.exists(path):
            if file_sha256(path) == new_sha:
                if self.manifest.get(rel) != new_sha:
                    self.manifest[rel] = new_sha
                    self._save_manifest()
                return 'unchanged'
            if not self._may_replace(rel, path):
                self.skipped.append(rel)
                return 'skipped'
            self._backup(rel, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        put(path)
        self.manifest[rel] = new_sha
        self._save_manifest()
        return 'written'

    def write(self, path, data):
        """Writes data at path unless the file there was edited since the generator wrote it."""
        def put(p):
            with open(p, 'wb') as f:
                f.write(data)
        return self._place(path, sha256(data), put)

    def replace(self, path, data):
        """Writes data at path, backing up a file there with other bytes first."""
        rel = self.rel(path)
        result = 'written'
        if os.path.exists(path):
            if file_sha256(path) == sha256(data):
                return 'unchanged'
            self._backup(rel, path)
            result = 'replaced'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)
        return result

    def install(self, source, path):
        """Moves the file at source (a fresh render) to path by the same rules; source is removed either way."""
        result = self._place(path, file_sha256(source), lambda p: shutil.move(source, p))
        if os.path.exists(source):
            os.remove(source)
        return result

    def edited(self):
        """Generated files whose hash no longer matches the manifest."""
        out = []
        for rel, sha in sorted(self.manifest.items()):
            path = os.path.join(self.root, rel)
            if os.path.exists(path) and file_sha256(path) != sha:
                out.append(rel)
        return out
