import json
import os
import sqlite3
from pathlib import Path
from .model import Section

APP_DIR=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'uiu-smart-routines'

class Store:
    def __init__(self,path=None):
        self.path=Path(path or APP_DIR/'routine.sqlite3')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path)
        self.db.execute('CREATE TABLE IF NOT EXISTS offerings (dataset TEXT, program TEXT, code TEXT, section TEXT, payload TEXT, PRIMARY KEY(dataset, program, code, section))')
        self.db.execute('CREATE TABLE IF NOT EXISTS routines (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, dataset TEXT, favorite INTEGER DEFAULT 0, payload TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP)')
        self.db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT)')
        self.db.commit()

    def import_sections(self,sections,dataset='Fall 2026'):
        with self.db:
            self.db.execute('DELETE FROM offerings WHERE dataset=?',(dataset,))
            self.db.executemany('INSERT INTO offerings VALUES (?,?,?,?,?)',[(dataset,s.program,s.code,s.section,json.dumps(s.to_dict())) for s in sections])
            self.db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)',('active_dataset',dataset))

    def datasets(self):
        return [x[0] for x in self.db.execute('SELECT DISTINCT dataset FROM offerings ORDER BY dataset DESC')]

    def sections(self,dataset=None,program=None):
        dataset=dataset or self.active_dataset()
        sql='SELECT payload FROM offerings WHERE dataset=?';args=[dataset]
        if program:sql+=' AND program=?';args.append(program)
        sql+=' ORDER BY code, section'
        return [Section.from_dict(json.loads(x[0])) for x in self.db.execute(sql,args)]

    def active_dataset(self):
        row=self.db.execute("SELECT value FROM meta WHERE key='active_dataset'").fetchone()
        return row[0] if row else 'Fall 2026'

    def save(self,name,sections,dataset=None,favorite=False):
        from .scheduler import verify
        problems=verify(sections)
        if problems:raise ValueError(f'Cannot save invalid routine: {problems[:3]}')
        with self.db:
            return self.db.execute('INSERT INTO routines(name,dataset,favorite,payload) VALUES(?,?,?,?)',
               (name,dataset or self.active_dataset(),int(favorite),json.dumps([s.to_dict() for s in sections]))).lastrowid

    def list_routines(self):
        return list(self.db.execute('SELECT id,name,dataset,favorite,created FROM routines ORDER BY favorite DESC,id DESC'))

    def load(self,id):
        row=self.db.execute('SELECT payload FROM routines WHERE id=?',(id,)).fetchone()
        if not row:raise KeyError(id)
        return [Section.from_dict(x) for x in json.loads(row[0])]

    def favorite(self,id,state):
        with self.db:self.db.execute('UPDATE routines SET favorite=? WHERE id=?',(int(state),id))

    def delete(self,id):
        with self.db:self.db.execute('DELETE FROM routines WHERE id=?',(id,))
