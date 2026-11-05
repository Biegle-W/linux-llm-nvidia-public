"""Install only the guarded ComfyUI desktop shortcut; preserve existing apps."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
def content(name, model):
    return '\n'.join([
        '[Desktop Entry]','Type=Application','Name='+name,
        'Comment=GPU-resident image workflow; open http://127.0.0.1:8188 after readiness',
        'Exec=/usr/bin/python3 "'+str(ROOT/'scripts/visible_terminal.py')+'" foreground --title "'+name+'" -- /usr/bin/python3 "'+str(ROOT/'scripts/comfy_run.py')+'" --model '+model+' --serve --foreground-backend',
        'Path='+str(ROOT),'Terminal=true','Icon=applications-graphics','Categories=Graphics;',''])

for name,model in [('ComfyUI Qwen Turbo','qwen-image-2.1-turbo'),('ComfyUI FLUX3 Klein','flux3-klein')]:
    desktop=Path.home()/'Desktop'/(name+'.desktop')
    text=content(name,model)
    if desktop.exists() and desktop.read_text()!=text:
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
