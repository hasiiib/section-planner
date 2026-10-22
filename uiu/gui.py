"""Native PySide6 UI. All operations and imported data remain on-device."""
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QEvent, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,
    QPushButton,QStackedWidget,QLineEdit,QComboBox,QListWidget,QTableWidget,QTableWidgetItem,
    QFileDialog,QMessageBox,QProgressBar,QSplitter,QHeaderView,QDialog,QScrollArea,QFrame,
    QGraphicsDropShadowEffect,QCheckBox,QListWidgetItem,QSizePolicy)
from .importers import import_offerings, SUPPORTED
from .storage import Store
from .scheduler import generate_preferred,time_label,verify
from .model import DAYS
from .exports import export

STYLE='''
QWidget{font-family:'Noto Sans','DejaVu Sans',sans-serif;font-size:12px;color:#263044;background:#FAFBFD}
QLabel{background:transparent}QMainWindow,QStackedWidget{background:#FAFBFD}
QPushButton{background:#F47721;color:white;border:0;border-radius:13px;padding:11px 19px;font-weight:700}
QPushButton:hover{background:#DF6215}QPushButton:pressed{background:#BB4A0A}
QPushButton:disabled{background:#ECEFF4;color:#949BA8}
QPushButton#secondary{background:white;color:#C95711;border:1px solid #F4CDB2}
QPushButton#secondary:hover{background:#FFF1E5}
QPushButton#iconButton{background:#FFF1E5;color:#BD530D;border:1px solid #F5D5BD;padding:10px;border-radius:12px}
QPushButton#iconButton:hover{background:#FFE2CA}
QLineEdit,QComboBox,QListWidget,QTableWidget{border:1px solid #E1E6EF;border-radius:12px;padding:8px;background:white;selection-background-color:#FFE1CA}
QComboBox{padding-right:22px}QComboBox::drop-down{border:none;width:26px}
QComboBox QAbstractItemView{background:white;border:1px solid #EDB185;selection-background-color:#FFE6D3;padding:6px}
QTableWidget{gridline-color:#E8ECF2;alternate-background-color:#FFF9F4}
QHeaderView::section{background:#FFF0E4;color:#964615;padding:9px;border:0;font-weight:700}
QProgressBar{border:none;border-radius:8px;height:15px;background:#F0E9E5;color:#333A46;text-align:center;font-weight:bold}
QProgressBar::chunk{background:#F47721;border-radius:8px}
QScrollArea{border:0;background:transparent}
QScrollBar:vertical{width:13px;background:#FFF4EB;margin:3px;border-radius:6px}
QScrollBar::handle:vertical{background:#F47721;border-radius:6px;min-height:36px}
QScrollBar::handle:vertical:hover{background:#DA5C0C}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px}
QScrollBar:horizontal{height:13px;background:#FFF4EB;margin:3px;border-radius:6px}
QScrollBar::handle:horizontal{background:#F47721;border-radius:6px;min-width:36px}
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{width:0px}
QFrame#routineCard{background:white;border:1px solid #E2E7F0;border-radius:18px}
'''

def label(text,size=0):
    w=QLabel(text);w.setWordWrap(True)
    if size:w.setStyleSheet(f'font-size:{size}px;font-weight:750')
    return w

def button(text,secondary=False):
    b=QPushButton(text);b.setCursor(Qt.CursorShape.PointingHandCursor)
    if secondary:b.setObjectName('secondary')
    return b

def clear_layout(layout):
    while layout.count():
        item=layout.takeAt(0)
        if item.widget():item.widget().deleteLater()
        elif item.layout():clear_layout(item.layout())

def section_periods(s):
    return '  |  '.join(f'{m.day} {time_label(m.start)}–{time_label(m.end)}  ·  {m.room or "Room not listed"}' for m in s.meetings)

class Work(QThread):
    found=Signal(object);progress=Signal(int,int);done=Signal(int,int,bool)
    def __init__(self,groups):super().__init__();self.groups=groups;self.stopping=False
    def run(self):
        try:
            v,b,complete,_=generate_preferred(self.groups,self.found.emit,cancelled=lambda:self.stopping,
                on_progress=lambda n,t:self.progress.emit(n,t))
            self.done.emit(v,b,complete)
        except Exception:
            self.done.emit(0,0,False)

class WelcomeButton(QPushButton):
    def __init__(self):
        super().__init__('START  →');self.setFixedSize(174,174)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet('QPushButton{background:#F47721;color:white;font-weight:900;font-size:22px;border-radius:87px;border:7px solid #FFDFCB}QPushButton:hover{background:#E35F10;border-color:#FBC69C}')
        glow=QGraphicsDropShadowEffect(self);glow.setColor(QColor(244,119,33,135));glow.setBlurRadius(39);glow.setOffset(0,9);self.setGraphicsEffect(glow)
        self.anim=QPropertyAnimation(glow,b'blurRadius',self);self.anim.setDuration(700);self.anim.setStartValue(28.0);self.anim.setKeyValueAt(.5,62.0);self.anim.setEndValue(39.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    def enterEvent(self,event):self.anim.start();super().enterEvent(event)

class RoutineTable(QTableWidget):
    def __init__(self,routine,zoom=1.0,parent=None):
        super().__init__(parent)
        self.zoom=zoom
        columns=['Day','Class Period','Course Code','Course Title','Section','Faculty','Room']
        entries=sorted(((DAYS.index(m.day),m.start,m.day,f'{time_label(m.start)} – {time_label(m.end)}',s.code,s.title,s.section,s.faculty,m.room) for s in routine for m in s.meetings))
        self.setColumnCount(len(columns));self.setHorizontalHeaderLabels(columns)
        self.setRowCount(len(entries));self.setEditTriggers(self.EditTrigger.NoEditTriggers)
        self.setSelectionMode(self.SelectionMode.NoSelection)
        self.setWordWrap(True);self.verticalHeader().hide();self.setAlternatingRowColors(True)
        px=int(11*zoom);f=self.font();f.setPointSize(max(8,px));self.setFont(f)
        for i,e in enumerate(entries):
            for j,value in enumerate(e[2:]):
                cell=QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignHCenter if j==0 else Qt.AlignmentFlag.AlignLeft))
                self.setItem(i,j,cell)
        i=0
        while i<len(entries):
            j=i+1
            while j<len(entries) and entries[j][2]==entries[i][2]:j+=1
            if j-i>1:self.setSpan(i,0,j-i,1)
            i=j
        widths=[63,175,126,245,83,185,145]
        for col,w in enumerate(widths):self.setColumnWidth(col,int(w*zoom))
        for i,e in enumerate(entries):
            long=max(len(str(e[5])),len(str(e[7])))
            self.setRowHeight(i,int((52 if long<31 else 72)*zoom))
        self.horizontalHeader().setMinimumSectionSize(50)
        self.setMinimumHeight(min(730,int((72+sum(self.rowHeight(i) for i in range(len(entries)))))))
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.store=Store();self.sections=[];self.selected=[];self.routines=[]
        self.worker=None;self.rendered=0;self.cards=[];self.zoom=1.0;self.warnings_data=[];self._cols=0;self._warning_pulse=False
        self.setWindowTitle('Section Planner');self.resize(1450,900)
        root_widget=QWidget();self.setCentralWidget(root_widget);root=QVBoxLayout(root_widget);root.setContentsMargins(24,20,24,16);root.setSpacing(13)
        self.progress=QProgressBar();self.progress.setRange(0,3);self.progress.setTextVisible(False);root.addWidget(self.progress)
        self.pages=QStackedWidget();root.addWidget(self.pages,1)
        for method in (self.welcome_page,self.import_page,self.course_page,self.results_page):
            page=QWidget();layout=QVBoxLayout(page);layout.setSpacing(13);self.pages.addWidget(page);method(layout)
        self.nav=QWidget();nav=QHBoxLayout(self.nav);nav.setContentsMargins(0,0,0,0)
        self.back=button('← Back',True);nav.addWidget(self.back);nav.addStretch()
        self.next=button('Next →');nav.addWidget(self.next);root.addWidget(self.nav)
        self.back.clicked.connect(lambda:self.go(self.pages.currentIndex()-1))
        self.next.clicked.connect(self.next_action)
        self.reload_store()
        default=Path(__file__).resolve().parent.parent/'Fall_2026_offerings.pdf'
        if not self.sections and default.exists():self.import_path(default,quiet=True)
        self.go(0)
        QApplication.instance().installEventFilter(self)

    def welcome_page(self,lay):
        lay.addStretch(2)
        t=label('Section Planner',36);t.setAlignment(Qt.AlignmentFlag.AlignCenter);lay.addWidget(t)
        sub=label('Find the right sections. Build your ideal routine.');sub.setAlignment(Qt.AlignmentFlag.AlignCenter);sub.setStyleSheet('color:#788394;font-size:15px');lay.addWidget(sub)
        row=QHBoxLayout();row.addStretch();start=WelcomeButton();row.addWidget(start);row.addStretch();lay.addSpacing(32);lay.addLayout(row)
        start.clicked.connect(lambda:self.go(1));lay.addStretch(3)
        credit=label('Made by Ayon');credit.setAlignment(Qt.AlignmentFlag.AlignRight);credit.setStyleSheet('color:#9199A8;font-size:11px');lay.addWidget(credit)

    def import_page(self,lay):
        lay.addStretch(1)
        title=label('Import your course offerings',25);title.setAlignment(Qt.AlignmentFlag.AlignCenter);lay.addWidget(title)
        small=label('PDF · DOC/DOCX · XLS/XLSX · CSV');small.setAlignment(Qt.AlignmentFlag.AlignCenter);small.setStyleSheet('color:#848D9C');lay.addWidget(small)
        row=QHBoxLayout();row.addStretch(1)
        self.import_button=button('↥   Open File');self.import_button.setMinimumSize(245,90)
        self.import_button.setStyleSheet('QPushButton{background:#F47721;color:white;font-size:20px;font-weight:850;border-radius:23px;border:3px solid #FFDFCA}QPushButton:hover{background:#E36616;border:3px solid #FCC595}')
        effect=QGraphicsDropShadowEffect(self.import_button);effect.setColor(QColor(244,119,33,105));effect.setBlurRadius(35);effect.setOffset(0,7);self.import_button.setGraphicsEffect(effect)
        animation=QPropertyAnimation(effect,b'blurRadius',self.import_button);animation.setDuration(1400);animation.setStartValue(18.0);animation.setKeyValueAt(.5,45.0);animation.setEndValue(18.0);animation.setLoopCount(-1);animation.start();self._import_animation=animation
        row.addWidget(self.import_button);row.addStretch(1);lay.addSpacing(15);lay.addLayout(row)
        self.import_button.clicked.connect(self.pick_file)
        self.import_info=label('Choose a supported course-offering file.');self.import_info.setAlignment(Qt.AlignmentFlag.AlignCenter);lay.addWidget(self.import_info)
        controls=QHBoxLayout();controls.addStretch();self.warning_btn=button('⚠  Warnings',True);self.warning_btn.setObjectName('iconButton');self.warning_btn.clicked.connect(self.show_warnings)
        controls.addWidget(self.warning_btn);controls.addStretch();lay.addLayout(controls)
        self.dataset_select=QComboBox();self.dataset_select.currentTextChanged.connect(self.switch_dataset)
#        lay.addWidget(label('Previously imported datasets',13));lay.addWidget(self.dataset_select);lay.addStretch(2)
        self.warning_timer=QTimer(self);self.warning_timer.timeout.connect(self.pulse_warning);self.warning_timer.start(900)
        self.set_warning_state([])

    def course_page(self,lay):
        head=QHBoxLayout();head.addWidget(label('Choose your courses',23));head.addStretch()
        self.filter_btn=button('⚙  Filter: All',True);self.filter_btn.clicked.connect(self.choose_filter);head.addWidget(self.filter_btn);lay.addLayout(head)
        self.filter_name='All';self.search=QLineEdit();self.search.setPlaceholderText('Search course code or title...');self.search.textChanged.connect(self.refresh_catalog);lay.addWidget(self.search)
        split=QSplitter();lay.addWidget(split,1)
        left=QWidget();lv=QVBoxLayout(left);lv.addWidget(label('Available courses',14));self.catalog=QListWidget();lv.addWidget(self.catalog);split.addWidget(left)
        mid=QWidget();mv=QVBoxLayout(mid);mv.addWidget(label('Available sections & class periods',14))
        self.section_table=QTableWidget(0,5);self.section_table.setHorizontalHeaderLabels(['Section','Faculty','Class Period','Credit','Program'])
        self.section_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.section_table.setWordWrap(True)
        self.section_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        mv.addWidget(self.section_table);add=button('+ Add Course');mv.addWidget(add);add.clicked.connect(self.add_course);split.addWidget(mid)
        right=QWidget();rv=QVBoxLayout(right);rv.addWidget(label('Selected courses',14));self.chosen=QListWidget();rv.addWidget(self.chosen)
        remove=button('Remove Selected',True);rv.addWidget(remove);remove.clicked.connect(self.remove_course);split.addWidget(right)
        split.setStretchFactor(0,2);split.setStretchFactor(1,4);split.setStretchFactor(2,2)
        self.catalog.currentRowChanged.connect(self.show_sections)
        self.selected_label=label('0 courses selected');lay.addWidget(self.selected_label)
        self.gen_panel=QWidget();p=QVBoxLayout(self.gen_panel);p.setContentsMargins(0,0,0,0)
        r=QHBoxLayout();self.gen_status=label('Generating routines...');r.addWidget(self.gen_status);r.addStretch()
        self.cancel_btn=button('Cancel',True);self.cancel_btn.clicked.connect(self.cancel);r.addWidget(self.cancel_btn);p.addLayout(r)
        self.gen_bar=QProgressBar();self.gen_bar.setRange(0,0);p.addWidget(self.gen_bar);lay.addWidget(self.gen_panel);self.gen_panel.hide()

    def results_page(self,lay):
        row=QHBoxLayout();row.addWidget(label('Class Routines',23));row.addStretch()
        compare=button('⇄  Compare',True);compare.clicked.connect(self.compare);row.addWidget(compare);lay.addLayout(row)
        self.results_status=label('No routines generated yet');lay.addWidget(self.results_status)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);lay.addWidget(self.scroll,1)
        self.host=QWidget();self.card_layout=QGridLayout(self.host);self.card_layout.setSpacing(17);self.scroll.setWidget(self.host)
        self.more=button('Show More Routines ↓',True);self.more.clicked.connect(self.show_more);lay.addWidget(self.more);self.more.hide()
        self.scroll.verticalScrollBar().valueChanged.connect(self._maybe_load)

    def go(self,index):
        if not 0<=index<=3:return
        if index==2 and not self.sections:
            QMessageBox.warning(self,'Import required','Upload a valid course-offering file first.');return
        self.pages.setCurrentIndex(index)
        self.progress.setVisible(index!=0);self.progress.setValue(index)
        self.nav.setVisible(index in (1,2,3))
        self.back.setVisible(index!=0)
        self.next.setVisible(index in (1,2));self.next.setText('Generate Routines' if index==2 else 'Next →')
        if index==2:self.refresh_catalog();self.refresh_selected()
        if index==3:self.refresh_results()

    def next_action(self):
        idx=self.pages.currentIndex()
        if idx==1:
            if not self.sections:QMessageBox.warning(self,'Invalid file','Import a valid class routine offering file first.');return
            self.go(2)
        elif idx==2:self.generate()

    def reload_store(self):
        self.dataset_select.blockSignals(True);self.dataset_select.clear();self.dataset_select.addItems(self.store.datasets());self.dataset_select.blockSignals(False)
        self.sections=self.store.sections();self.refresh_catalog()

    def switch_dataset(self,name):
        if name:
            self.sections=self.store.sections(name);self.selected.clear();self.routines.clear();self.refresh_catalog();self.refresh_selected()

    def pick_file(self):
        filters='Supported files (*.pdf *.doc *.docx *.xls *.xlsx *.csv);;PDF (*.pdf);;Word (*.doc *.docx);;Excel (*.xls *.xlsx);;CSV (*.csv)'
        path,_=QFileDialog.getOpenFileName(self,'Import course offerings',str(Path.home()),filters)
        if path:self.import_path(Path(path))

    def import_path(self,path,quiet=False):
        try:
            sections,warnings,pages,trimester=import_offerings(path)
            if not sections:raise ValueError('No valid course offerings found.')
            name=trimester or Path(path).stem
            self.store.import_sections(sections,name);self.reload_store();self.dataset_select.setCurrentText(name)
            self.sections=sections;self.selected=[];self.routines=[]
            self.import_info.setText(f'{name}  •  {len(sections)} sections  •  {len({(s.program,s.code) for s in sections})} courses')
            self.set_warning_state(warnings)
            if not quiet:self.go(2)
        except Exception as exc:
            if not quiet:QMessageBox.warning(self,'Invalid or unsupported file',str(exc)+'\n\nPlease upload a supported course-offering file.')

    def set_warning_state(self,warnings):
        self.warnings_data=list(warnings)
        self.warning_btn.setText(f'⚠  {len(warnings)} Warnings' if warnings else '✓  No warnings')
        if warnings:self.warning_btn.setStyleSheet('QPushButton{background:#FFF1DB;color:#B45309;border:2px solid #FFAE42;border-radius:13px;font-weight:bold;padding:11px}QPushButton:hover{background:#FFE5BB}')
        else:self.warning_btn.setStyleSheet('')

    def pulse_warning(self):
        if not self.warnings_data:return
        self._warning_pulse=not self._warning_pulse
        border="#F59E0B" if self._warning_pulse else "#FF6B00"
        self.warning_btn.setStyleSheet(f"QPushButton{{background:#FFF1DB;color:#A54A08;border:2px solid {border};border-radius:13px;font-weight:bold;padding:11px}}")

    def show_warnings(self):
        if not self.warnings_data:QMessageBox.information(self,'Import checks','No warnings reported.');return
        dialog=QDialog(self);dialog.setWindowTitle('Import warnings');dialog.resize(790,500)
        lay=QVBoxLayout(dialog);lay.addWidget(label(f'{len(self.warnings_data)} source data warnings',17))
        listwidget=QListWidget();listwidget.addItems(self.warnings_data);lay.addWidget(listwidget)
        close=button('Close');close.clicked.connect(dialog.accept);lay.addWidget(close);dialog.exec()

    def choose_filter(self):
        menu=QDialog(self);menu.setWindowTitle('Filter programs');box=QVBoxLayout(menu);box.addWidget(label('Filter available courses',17))
        for choice in ['All']+sorted({s.program for s in self.sections}):
            b=button(('✓  ' if choice==self.filter_name else '')+choice,True)
            b.clicked.connect(lambda checked=False,ch=choice:(setattr(self,'filter_name',ch),self.filter_btn.setText('⚙  Filter: '+ch),self.refresh_catalog(),menu.accept()))
            box.addWidget(b)
        menu.exec()

    def refresh_catalog(self):
        if not hasattr(self,'catalog'):return
        query=self.search.text().casefold();options={}
        for s in self.sections:
            if self.filter_name!='All' and s.program!=self.filter_name:continue
            options[(s.program,s.code)]=s.title
        self.catalog_keys=[key for key,title in sorted(options.items()) if query in (' '.join(key)+' '+title).casefold()]
        self.catalog.clear();self.catalog.addItems([f'{p} · {c}  |  {options[(p,c)]}' for p,c in self.catalog_keys])

    def show_sections(self,index):
        if index<0 or index>=len(self.catalog_keys):self.section_table.setRowCount(0);return
        key=self.catalog_keys[index];sections=[s for s in self.sections if (s.program,s.code)==key]
        self.section_table.setRowCount(len(sections))
        for row,s in enumerate(sections):
            for col,value in enumerate([s.section,s.faculty,section_periods(s),s.credit,s.program]):self.section_table.setItem(row,col,QTableWidgetItem(str(value)))
            self.section_table.setRowHeight(row,65 if len(s.meetings)>1 else 47)

    def add_course(self):
        index=self.catalog.currentRow()
        if index<0:return
        key=self.catalog_keys[index]
        if key not in self.selected:self.selected.append(key)
        self.refresh_selected()

    def remove_course(self):
        index=self.chosen.currentRow()
        if index>=0:self.selected.pop(index);self.refresh_selected()

    def refresh_selected(self):
        if not hasattr(self,'chosen'):return
        names={(s.program,s.code):s.title for s in self.sections}
        self.chosen.clear();self.chosen.addItems([f'{p} · {c}\n{names.get((p,c),"")}' for p,c in self.selected])
        self.selected_label.setText(f'{len(self.selected)} courses selected')

    def generate(self):
        if self.worker and self.worker.isRunning():return
        if not self.selected:QMessageBox.warning(self,'No courses','Select at least one course.');return
        groups=[[s for s in self.sections if (s.program,s.code)==key] for key in self.selected]
        self.routines=[];self.gen_panel.show();self.gen_bar.setRange(0,0)
        self.next.setEnabled(False);self.back.setEnabled(False)
        self.worker=Work(groups);self.worker.found.connect(self.routines.append);self.worker.progress.connect(self.generation_progress)
        self.worker.done.connect(self.generation_done);self.worker.start()

    def generation_progress(self,n,total):
        if total:
            self.gen_bar.setRange(0,100);self.gen_bar.setValue(min(99,int(n*100/total)))
            self.gen_status.setText(f'Generating... {len(self.routines):,} routines found')

    def cancel(self):
        if self.worker:self.worker.stopping=True;self.gen_status.setText('Cancelling generation...')

    def generation_done(self,valid,rejected,complete):
        self.next.setEnabled(True);self.back.setEnabled(True);self.gen_panel.hide()
        if complete:
            self.results_status.setText(f'Completed · {valid:,} valid routines · {rejected:,} skipped branches')
            if not valid:QMessageBox.information(self,'No valid routines','No conflict-free section combination exists for the selected courses.')
            self.go(3)
        else:
            QMessageBox.information(self,'Generation interrupted',f'Generation stopped after finding {valid:,} routines. These are partial results, not a completed enumeration.')

    def refresh_results(self):
        for frame in self.cards:frame.setParent(None);frame.deleteLater()
        self.cards.clear();clear_layout(self.card_layout);self.rendered=0;self._cols=0
        if not self.routines:self.more.hide();return
        self._fill_batch()

    def _fill_batch(self):
        end=min(len(self.routines),self.rendered+15)
        for i in range(self.rendered,end):self.cards.append(self.make_card(i))
        self.rendered=end;self.reflow()
        self.more.setVisible(end<len(self.routines))
        self.more.setText(f'Show More Routines  ({end:,} / {len(self.routines):,})')

    def show_more(self):self._fill_batch()

    def _maybe_load(self,value):
        scroll=self.scroll.verticalScrollBar()
        if self.pages.currentIndex()==3 and self.more.isVisible() and value>=scroll.maximum()-180:
            QTimer.singleShot(50,self._fill_batch)

    def make_card(self,index):
        frame=QFrame();frame.setObjectName('routineCard');frame.setMinimumWidth(525)
        outer=QVBoxLayout(frame);outer.setContentsMargins(13,12,13,15)
        head=QHBoxLayout();head.addWidget(label(f'Routine {index+1}',17));head.addStretch()
        save=button('↧  Save / Export',True);save.setToolTip('Export this routine as PDF, PNG, XLSX or CSV')
        save.clicked.connect(lambda checked=False,i=index:self.export_one(i));head.addWidget(save);outer.addLayout(head)
        t=RoutineTable(self.routines[index],self.zoom);outer.addWidget(t);frame.table=t
        return frame

    def export_one(self,index):
        if index>=len(self.routines):return
        routine=self.routines[index]
        target,_=QFileDialog.getSaveFileName(self,'Export Class Routine',f'Class_Routine_{index+1}.pdf','PDF (*.pdf);;PNG (*.png);;Excel (*.xlsx);;CSV (*.csv)')
        if not target:return
        try:
            export(routine,target)
            self.store.save(f'Routine {index+1}',routine,self.dataset_select.currentText())
            QMessageBox.information(self,'Exported',f'Routine {index+1} exported successfully. A local saved copy was also created.')
        except Exception as exc:QMessageBox.critical(self,'Export failed',str(exc))

    def reflow(self):
        if not hasattr(self,'scroll'):return
        width=self.scroll.viewport().width()
        columns=max(1,min(3,width//1080))
        if columns==self._cols and self.card_layout.count()==len(self.cards):return
        self._cols=columns
        for card in self.cards:self.card_layout.removeWidget(card)
        for i,card in enumerate(self.cards):self.card_layout.addWidget(card,i//columns,i%columns)
        for col in range(3):self.card_layout.setColumnStretch(col,1 if col<columns else 0)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'scroll'):QTimer.singleShot(25,self.reflow)

    def eventFilter(self,obj,event):
        if event.type()==QEvent.Type.Wheel and event.modifiers() & Qt.KeyboardModifier.ControlModifier and self.pages.currentIndex()==3:
            delta=event.angleDelta().y()
            if delta:
                self.zoom=max(.7,min(1.8,round(self.zoom+(0.1 if delta>0 else -.1),2)))
                for i,frame in enumerate(self.cards):
                    lay=frame.layout();old=frame.table;lay.removeWidget(old);old.deleteLater()
                    t=RoutineTable(self.routines[i],self.zoom);frame.table=t;lay.addWidget(t)
                return True
        return super().eventFilter(obj,event)

    def compare(self):
        if len(self.routines)<2:QMessageBox.information(self,'Compare routines','At least two routines are required.');return
        picker=QDialog(self);picker.setWindowTitle('Choose routines to compare');picker.resize(430,520)
        form=QVBoxLayout(picker);form.addWidget(label('Choose two or more routines',18))
        chooser=QListWidget();chooser.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for i in range(len(self.routines)):chooser.addItem(f'Routine {i+1}')
        form.addWidget(chooser);run=button('Compare Selected');form.addWidget(run)
        run.clicked.connect(picker.accept)
        if not picker.exec():return
        indices=[x.row() for x in chooser.selectedIndexes()]
        if len(indices)<2:QMessageBox.warning(self,'Selection required','Select at least two routines.');return
        dialog=QDialog(self);dialog.setWindowTitle('Compare routines');dialog.resize(1250,720)
        layout=QVBoxLayout(dialog);scroller=QScrollArea();scroller.setWidgetResizable(True);layout.addWidget(scroller)
        container=QWidget();row=QHBoxLayout(container)
        for i in indices:row.addWidget(self.make_compare_card(i))
        scroller.setWidget(container);close=button('Close');close.clicked.connect(dialog.accept);layout.addWidget(close);dialog.exec()

    def make_compare_card(self,index):
        frame=QFrame();frame.setObjectName('routineCard');lay=QVBoxLayout(frame)
        lay.addWidget(label(f'Routine {index+1}',18));lay.addWidget(RoutineTable(self.routines[index],self.zoom));return frame
