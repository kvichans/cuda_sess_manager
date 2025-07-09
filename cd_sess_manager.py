''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.0.14 2025-07-09'
'''
import  os, json, configparser, itertools
import  cudatext     as app
import  cudatext_cmd as cmds
import  cudax_lib    as apx
from    .cd_plug_lib    import *

_ = get_translation(__file__)  # I18N

pass;                           LOG     = (-1== 1)  # Do or dont logging.
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)

CDSESS_EXT      = '.cuda-session'
SWSESS_EXT      = '.synw-session'
SESS_JSON       = os.path.join(app.app_path(app.APP_DIR_SETTINGS), 'cuda_sess_manager.json')
SESS_DEFAULT    = 'default'+CDSESS_EXT if app.app_api_version() >= '1.0.464' else 'history session.json'

# Localization
NEED_NEWER_API  = _('Plugin needs newer app version')
NO_RECENT       = _('No recent sessions')
NO_PREV         = _('No previous session')
SAVED           = _('Session "{stem}" is saved')
OPENED          = _('Session "{stem}" is opened')
CREATE_ASK      = _('Session "{stem}" not found\n\nCreate it?')
CREATED         = _('Session "{stem}" is created')
DLG_ALL_FILTER  = _('CudaText sessions|*{}|SynWrite sessions|*{}|All files|*.*').format(CDSESS_EXT, SWSESS_EXT)
DLG_CUD_FILTER  = _('CudaText sessions|*{}').format(CDSESS_EXT)

IS_UNIX 		= os.name=='posix'
HOMEDIR 		= os.path.expanduser('~/') if IS_UNIX else ''

def nice_name(fn):
    s1 = juststem(fn)
    s2 = os.path.dirname(fn)
    if IS_UNIX:
        if s2.startswith(HOMEDIR):
            s2 = '~/'+s2[len(HOMEDIR):]
    return s1+'\t'+s2 

class Command:
    def recent(self):
        ''' Show list, use user select '''
        if not _checkAPI(): return
        sess    = self._loadSess(existing=True)
        rcnt    = sess['recent']
        if 0==len(rcnt):
            return app.msg_status(NO_RECENT)
        ssmenu  = [nice_name(sfile) for sfile in rcnt]
        opt_n   = 0 if app.app_api_version()<'1.0.233' else app.DMENU_NO_FULLFILTER
        ans     = app.dlg_menu(app.DMENU_LIST + opt_n, ssmenu)
        if ans is None: return
        self.open(rcnt[ans])

    def on_open_pre(self, ed_self, filename):
        ''' Handle editor event '''
        pass;                   log("filename={}",(filename))   if LOG else 0
        if filename.endswith(CDSESS_EXT) or filename.endswith(SWSESS_EXT):
            pass               #print('Opening session: '+filename)
            confirm = apx.get_opt('session_manager_confirmation', 2)
            if confirm==0:
                as_sess = False
            elif confirm==1:
                as_sess = True
            else:
                ask = app.msg_box(_('File "%s" is a session file. Do you want to open the session (Yes) or open the raw content (No)?') \
                        % os.path.basename(filename), app.MB_YESNO + app.MB_ICONQUESTION)
                as_sess = ask==app.ID_YES
            if as_sess:
                self.open(filename)
                return False
            else:
                return True

    def open(self, ssnew=None):
        ''' Open new session from file ssnew or after user asking '''
        if not _checkAPI(): return True # Do more if need
        pass;                   log("ssnew={}",(ssnew))         if LOG else 0
#       in_dir      = app.app_path(app.APP_DIR_DATA)
        sscur       = app.app_path(app.APP_FILE_SESSION)
        pass;                   log("sscur={}",(sscur))         if LOG else 0
        if sscur==ssnew:
            self.top_sess(ssnew)
            pass;               log("sscur==ssnew",())          if LOG else 0
            return
        sscur_save  = app.app_proc(app.PROC_SAVE_SESSION, sscur)
        pass;                  #LOG and log('sscur_save={}',(sscur_save))
        if sscur_save == False:
            return
        if ssnew is None:
            ssnew   = app.dlg_file(is_open=True, filters=DLG_ALL_FILTER
                    , init_filename='!'     # '!' to disable check "filename exists"
                    , init_dir=     ''
                    )
        if ssnew is None: return
        if ssnew.endswith(SWSESS_EXT) and os.path.isfile(ssnew):
            # Import from Syn
            sssyn   = ssnew
            sscud   = ssnew[:-len(SWSESS_EXT)]+CDSESS_EXT
            if os.path.isfile(sscud):
                sscud   = app.dlg_file(is_open=False, filters=DLG_CUD_FILTER
                        , init_filename=os.path.basename(sscud)
                        , init_dir=     os.path.dirname( sscud)
                        )
                if not sscud: return
            if not import_syn_sess(sssyn, sscud): return
            ssnew   = sscud
            
        pass;                  #LOG and log('ssnew={}',(ssnew))
        ssnew       = apx.icase(False,''
                    ,   ssnew.endswith(CDSESS_EXT)  , ssnew
                    ,   os.path.isfile(ssnew)       , ssnew
                    ,   True                        , ssnew+CDSESS_EXT
                    )
        pass;                  #LOG and log('ssnew={}',(ssnew))
        if os.path.isfile(ssnew):
            # Open
            pass;               log("?? PROC_LOAD_SESSION",())   if LOG else 0
#           app.app_proc(app.PROC_SAVE_SESSION, sscur)
            self.forget(True) # avoid asking 'save modified tab?'
            ssnew_load  = app.app_proc(app.PROC_LOAD_SESSION, ssnew)
            pass;               log('ssnew_load={}',(ssnew_load))   if LOG else 0
            if ssnew_load == False:
                return
            app.app_proc(app.PROC_SET_SESSION,  ssnew)
            app.msg_status(OPENED.format(stem=juststem(ssnew)))
            self.top_sess(ssnew)
        else:
            # New
            pass;               log("?? new SESSION",())   if LOG else 0
            if app.ID_NO==app.msg_box(CREATE_ASK.format(stem=juststem(ssnew)), app.MB_YESNO):   return
#           app.app_proc(app.PROC_SAVE_SESSION, sscur)
            app.ed.cmd(cmds.cmd_FileCloseAll)
            app.app_proc(app.PROC_SET_SESSION,  ssnew)
            app.app_proc(app.PROC_SAVE_SESSION, ssnew)
            app.msg_status(CREATED.format(stem=juststem(ssnew)))
            self.top_sess(ssnew)
            return

    def close(self):
        sscur       = app.app_path(app.APP_FILE_SESSION)
        sscur_save  = app.app_proc(app.PROC_SAVE_SESSION, sscur)
        if sscur_save == False:
            return 
#       app.app_proc(app.PROC_SAVE_SESSION, sscur)
        app.app_proc(app.PROC_SET_SESSION, SESS_DEFAULT) # w/o path to use "settings" portable way
        pass;                  #LOG and log('ok',())

    def forget(self, clear_modified=False):
        app.app_proc(app.PROC_SET_SESSION, SESS_DEFAULT) # w/o path to use "settings" portable way

        if clear_modified:
            for h in app.ed_handles():
                e = app.Editor(h)
                e.set_prop(app.PROP_MODIFIED, False)

        app.ed.cmd(cmds.cmd_FileCloseAll)
        pass;                  #LOG and log('ok',())

    def openPrev(self, recent_pos=1):
        ''' Open session that was opened before.
            Params
                recent_pos  Position in recent list
        '''
        if not _checkAPI(): return
        sess    = self._loadSess(existing=True)
        rcnt    = sess['recent']
        if len(rcnt)<1+recent_pos:
            return app.msg_status(NO_PREV)
        self.open(rcnt[recent_pos])

    def save(self):
        ''' Save cur session to file '''
        if not _checkAPI(): return
        sscur       = app.app_path(app.APP_FILE_SESSION)
        sscur_save  = app.app_proc(app.PROC_SAVE_SESSION, sscur)
        if sscur_save == False:
            return 
#       app.app_proc(app.PROC_SAVE_SESSION, sscur)
        app.msg_status(SAVED.format(stem=juststem(sscur)))
        self.top_sess(sscur)

    def saveAs(self):
        ''' Save cur session to new file '''
        if not _checkAPI(): return
        sscur       = app.app_path(app.APP_FILE_SESSION)
        sscur_save  = app.app_proc(app.PROC_SAVE_SESSION, sscur)
        if sscur_save == False:
            return 
        pass;                   app.msg_status(sscur)
        (ssdir
        ,ssfname)   = os.path.split(sscur)
        ssfname     = ssfname.replace('.json', '')
        ssnew       = app.dlg_file(is_open=False, filters=DLG_CUD_FILTER
                    , init_filename=ssfname
                    , init_dir=     ssdir
                    )
        pass;                   app.msg_status(str(ssnew))
        if ssnew is None:   return
        ssnew       = apx.icase(False,''
                    ,   ssnew.endswith(CDSESS_EXT)  , ssnew
                    ,   os.path.isfile(ssnew)       , ssnew
                    ,   True                        , ssnew+CDSESS_EXT
                    )
        if os.path.normpath(sscur)==os.path.normpath(ssnew): return
#       app.app_proc(app.PROC_SAVE_SESSION, sscur)
        app.app_proc(app.PROC_SAVE_SESSION, ssnew)
        app.app_proc(app.PROC_SET_SESSION,  ssnew)
        app.msg_status(SAVED.format(stem=juststem(ssnew)))
        self.top_sess(ssnew)

    #################################################
    ## Private
    def top_sess(self, ssPath):
        ''' Set the session on the top of recent.
            Params:
                ssPath  Full path to session file
        '''
        ssPath  = os.path.normpath(ssPath)
        sess    = self._loadSess()
        rcnt    = sess['recent']
        if ssPath in rcnt:
            pos = rcnt.index(ssPath)
            if 0==pos:  return  # Already at top
            del rcnt[pos]
        rcnt.insert(0, ssPath)
        max_len = apx.get_opt('ui_max_history_menu', 10)
        del rcnt[max_len:]
        self._saveSess(sess)

    def _loadSess(self, existing=False):
        ''' See _saveSess for returned data format.
            Params
                existing    Delete path from recent if one doesnot exist
        '''
        sess    = apx._json_loads(open(SESS_JSON).read())   if os.path.exists(SESS_JSON) else self.dfltSess
#       sess    = json.loads(open(SESS_JSON).read())        if os.path.exists(SESS_JSON) else self.dfltSess
        rcnt    = sess['recent']
        if existing and 0<len(rcnt):
            sess['recent']  = list(filter(os.path.isfile, rcnt))
        return sess

    def _saveSess(self, sess):
        ''' sess py-format:
                {   'recent':[f1, f2, ...]      # Session fullpaths
                }
        '''
        open(SESS_JSON, 'w').write(json.dumps(sess, indent=2))

    def __init__(self):
        self.dfltSess   =   {'recent':[]}

def import_syn_sess(sssyn, sscud):
    """ Syn session ini-format
            [sess]
            gr_mode=4               Номер режима групп (1...)
                                        1 - one group
                                        2 - two horz
                                        3 - two vert
            gr_act=4                Номер активной группы (1..6)
            tab_act=0,0,1,2,0,0     Номера активных вкладок на каж группе (от 0, -1 значит нет вкладок)
            split=50                Позиция сплиттера (int в процентах), только для режимов 1*2, 2*1 и 1+2, иначе 50
            tabs=                   Число вкладок, оно только для оценки "много ли"
                Потом идут секции [f#] где # - номер вкладки от 0
            [f0]
            gr=                     Номер группы (1..6)
            fn=                     Имя файла utf8 (точку ".\" не парсить)
            top=10,20               Два числа - top line для master, slave
            caret=10,20             Два числа - каретка для master, slave
            wrap=0,0                Два bool (0/1) - wrap mode для master, slave
            prop=0,0,0,0,           4 числа через зап.
                - r/o (bool)
                - line nums visible (bool)
                - folding enabled (bool) - (NB! Было раньше disabled)
                - select mode (0..)
            color=                  Цвет таба (строка та же)
            colmark=                Col markers (строка та же)
            folded=                 2 строки через ";" - collapsed ranges для master, slave
    """
    cud_js  = {}
    cfgSyn  = configparser.ConfigParser()
    cfgSyn.read(sssyn, encoding='utf-8')
    for n_syn_tab in itertools.count():
        s_syn_tab   = f('f{}', n_syn_tab)
        if s_syn_tab not in cfgSyn: break#for n_syn_tab
        d_syn_tab   = cfgSyn[s_syn_tab]
        s_cud_tab   = f('{:03}', n_syn_tab)
        d_cud_tab   = cud_js.setdefault(s_cud_tab, {})
        d_cud_tab['file']   = d_syn_tab['fn']
        d_cud_tab['group']  = int(d_syn_tab['gr'])
       #for n_syn_tab
    cud_js['groups']    = max([t['group'] for t in cud_js.values()])
    pass;                      #LOG and log('cud_js=¶{}',pf(cud_js))
    open(sscud, 'w').write(json.dumps(cud_js, indent=2))
    return True
   #def import_syn_sess

def _checkAPI():
    if app.app_api_version()<'1.0.106':
        app.msg_status(NEED_NEWER_API)
        return False
    return True

#### Utils ####
def juststem(sspath):
    stem_ext    = os.path.basename(sspath)
    return stem_ext[:stem_ext.rindex('.')] if '.' in stem_ext else stem_ext
