"""Install only the guarded ComfyUI desktop shortcut; preserve existing apps."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
def legacy_content(name, model, video=False):
    return '\n'.join([
        '[Desktop Entry]','Type=Application','Name='+name,
        ('Comment=GPU-only video workflow; open http://127.0.0.1:8188 after readiness' if video else 'Comment=GPU-resident image workflow; open http://127.0.0.1:8188 after readiness'),
        'Exec=/usr/bin/python3 "'+str(ROOT/'scripts/visible_terminal.py')+'" foreground --title "'+name+'" -- /usr/bin/python3 "'+str(ROOT/'scripts/comfy_run.py')+'" --model '+model+(' --video-entry' if video else '')+' --serve --foreground-backend',
        'Path='+str(ROOT),'Terminal=true','Icon=applications-graphics','Categories=Graphics;',''])

def content(name,model,video=False):
    text=legacy_content(name,model,video)
    if not video:return text
    text=text.replace('Categories=Graphics;','Categories=Graphics;\nActions=720p;1080p;')
    base=next(line for line in text.splitlines() if line.startswith('Exec='))
    for resolution in ('720p','1080p'):
        text+='\n[Desktop Action '+resolution+']\nName='+resolution+' video\n'+base+' --video-resolution '+resolution+'\n'
    return text

def main():
    for name,model,video in [('ComfyUI Qwen Turbo','qwen-image-2.1-turbo',False),('ComfyUI FLUX3 Klein','flux3-klein',False),('ComfyUI Wan 2.2 5B','wan22-5b',True),('ComfyUI LTX 2.3 Mesh','ltx23-mesh',True)]:
        desktop=Path.home()/'Desktop'/(name+'.desktop')
        text=content(name,model,video)
        if desktop.exists() and desktop.read_text() not in (text,legacy_content(name,model,video)):
            raise SystemExit('Different existing shortcut preserved: '+desktop.name)
        desktop.write_text(text);desktop.chmod(0o755)
        subprocess.run(['desktop-file-validate',str(desktop)],check=True)
        subprocess.run(['gio','set',str(desktop),'metadata::trusted','true'],check=False)
        print('Installed Desktop-only '+name)

    # Retire only the exact generic shortcut created during this setup.
    old=Path.home()/'Desktop/ComfyUI Dual GPU.desktop'
    if old.exists():
        previous=content('ComfyUI Dual GPU','qwen-image-2.1-turbo').replace('Comment=GPU-resident image workflow;', 'Comment=Guarded GPU-resident image workflows;')
        if old.read_text()==previous:old.unlink()

if __name__=='__main__':main()
